from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, abort, redirect, flash, send_from_directory
import secrets, string
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, user_logged_in, login_required
from flask_sqlalchemy import SQLAlchemy
from bcrypt import gensalt, hashpw, checkpw
from PIL import Image
from datetime import datetime
import os
from flask_socketio import SocketIO, emit, send

app = Flask(__name__)
app.config['SECRET_KEY'] = "test" # ''.join([secrets.choice(string.printable) for _ in range(30)])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
socketio = SocketIO(app)

@login_manager.user_loader
def user_loader(id):
    return User.query.get(id)

maintenance_mode = False

@app.before_request
def check_maintenance():
    if request.path.startswith("/static"): return
    if maintenance_mode:
        if current_user.is_authenticated:
            flash("Die Seite ist aktuell unter Wartung -- Teile der Seite könnten nicht wie erwartet funktionieren")
        else:
            abort(503)



# --- MODELS ---

"""
:class: Aktion
    - id INTEGER (P.K. A)
    - name TEXT
    - datum DATE
    - body TEXT
    - img_url TEXT

:class: User
    - id INTEGER (P.K. A)
    - name TEXT
    - email TEXT
    - pronouns TEXT
    - password TEXT


"""


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    email = db.Column(db.VARCHAR(254))
    pronouns = db.Column(db.VARCHAR(120))
    password = db.Column(db.VARCHAR(540))
    rank = db.Column(db.Integer)
    posts = db.relationship('Blogeintrag', backref='author', lazy = True)



class Aktion(db.Model):
    _id = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    date = db.Column(db.DATETIME)
    body = db.Column(db.VARCHAR(10240))


class Torrent(db.Model):
    _id         = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name        = db.Column(db.VARCHAR(120))
    t_id        = db.Column(db.VARCHAR(120))
    info_hash   = db.Column(db.VARCHAR(120))
    seeders     = db.Column(db.Integer)
    peers       = db.Column(db.Integer)

    

class Blogeintrag(db.Model):
    __tablename__ = 'blogeintrag'
    _id = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    date = db.Column(db.DATETIME)
    body = db.Column(db.VARCHAR(10240))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# --- Error Handling ---

@app.errorhandler(401)
def unauthorized(*a):
    return redirect("/login")

@app.errorhandler(404)
def notfound(msg):
    return render_template('404.html', msg=msg)

@app.errorhandler(503)
def error_503(error):
    return render_template("maintenance.html") 

# --- Routing ---

@app.route("/")
def root():
    aktionen = Aktion.query.all()
    blogeintraege = Blogeintrag.query.all()
    return render_template("index.html", aktionen=aktionen, blogs=blogeintraege)

@app.route("/login")
def login():
    if current_user.is_authenticated: return redirect("/lj-backend")
    return render_template("anmeldung.html")


@app.route("/login", methods=["POST"])
def login_Post():
    email = request.form.get("email")
    passwd = request.form.get("password")
    user: User = User.query.filter_by(email = email).first()
    if not user:
        abort(401)
    if checkpw(passwd.encode(), user.password.encode()):
        login_user(user, request.form.get("remember-me"))
        return redirect("/lj-backend")

    return render_template("anmeldung.html")

@app.route("/signup")
def register():
    if current_user.is_authenticated: return redirect("/lj-backend")
    return render_template("register.html")

@app.route("/kontakt")
def ktk():
    return render_template("kontakt.html")

@app.route("/lj-aktionen/<id>")
def aktionsseite(id):
    akt = Aktion.query.get_or_404(id)
    return render_template("aktion.html", aktion=akt)

@app.route("/lj-blog/<id>")
def blogseite(id):
    blg = Blogeintrag.query.get_or_404(id)
    return render_template("blog_eintrag.html", aktion=blg)

@app.route("/lj-backend")
@login_required
def backend():
    return render_template("backend.html", aktionen = Aktion.query.all())

@app.route("/lj-backend/updata", methods=["POST"])
@login_required
def cache_clear():
    if current_user.rank < 5: abort(403)
    aktionen = Aktion.query.all()
    for ak in aktionen:
        if datetime.now() > ak.date: 
            os.remove(f'static/aktionen/{ak._id}.jpg')
            db.session.delete(ak)
    db.session.commit()
    return redirect("/lj-backend")

@app.route("/lj-backend/updata/delete/aktion/<int:id>", methods=["POST"])
@login_required
def aktion_loeschen(id):
    if current_user.rank < 5: abort(403)
    aktion = db.session.query(Aktion).get(id)
    os.remove(f'static/aktionen/{aktion._id}.jpg')
    db.session.delete(aktion)
    db.session.commit()
    return redirect("/lj-backend")

@app.route("/lj-backend/postdata/aktion", methods=["POST"])
@login_required
def neue_aktion():
    print(current_user)
    if current_user.rank < 5: abort(403)
    date = datetime.fromisoformat(request.form["activity-date"])
    aktion = Aktion(date=date, name = request.form["activity-title"], body = request.form["activity-description"])
    db.session.add(aktion)
    db.session.commit()
    if 'activity-image' in request.files:
        file = request.files['activity-image']
        if file.filename:
            file.save(f'temp/'+secure_filename(file.filename))
            
            img = Image.open(f'temp/'+secure_filename(file.filename))
            img.save(f'static/aktionen/{aktion._id}.jpg')
            img.close()
            os.remove(f'temp/'+secure_filename(file.filename))
    return redirect("/lj-backend")

@app.route("/lj-backend/devtools/toggle-maintenance", methods=["POST"])
@login_required
def wartung_an_aus():
    if current_user.rank < 8: abort(403)
    global maintenance_mode
    maintenance_mode = request.form.get('mt-mode')
    return redirect("/lj-backend")

@app.route("/lj-backend/postdata/beintrag", methods=["POST"])
@login_required
def neue_pm():
    print(current_user)
    if current_user.rank < 5: abort(403)
    date = datetime.now()
    aktion = Blogeintrag(date=date, name = request.form["pm-title"], body = request.form["pm-body"], author_id = current_user.id)
    db.session.add(aktion)
    db.session.commit()
    if 'activity-image' in request.files:
        file = request.files['activity-image']
        if file.filename:
            file.save(f'temp/'+secure_filename(file.filename))
            
            img = Image.open(f'temp/'+secure_filename(file.filename))
            img.save(f'static/aktionen/{aktion._id}.jpg')
            img.close()
            os.remove(f'temp/'+secure_filename(file.filename))
    return redirect("/lj-backend")


@app.route("/lj-backend/lj-tools/ljtt")
@login_required
def tracker():
    return render_template("torrent_tracker.html")

@app.route("/lj-backend/lj-torrentd")
@login_required
def new_torrent():
    return render_template("newtorrent.html")


kt = {}

ROOT = "localhost"
RP = 5000


@app.route("/mitmachen")
def mm():
    if current_user.is_authenticated:
        return redirect("/lj-backend")
    return """
<meta http-equiv="refresh" content"10;/login">
Hier könnten sich Neumitglieder*innen registrieren - Aber das ist noch nicht implementiert. Du wirst stattdessen weitergeleitet zur anmeldeseite<br>

Solltest du nicht nach wenigen sekunden weitergeleitet werden kommst du <a href="/login">hier</a> zur anmeldung
"""


if __name__ == "__main__":
    socketio.run(app, debug=True)
