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


from copy import deepcopy
from threading import Thread
from flask.wrappers import Request
import libtorrent as lt
from pickle import dumps
kt = {}

ROOT = "localhost"
RP = 5000

@socketio.on("am_i_done")
def aid(id):
    if os.path.exists(path := os.path.abspath(f"lt/{id}")) and len(os.listdir(path)) > 0:
        if os.path.exists(os.path.join(path, "magnet")):
            emit("gt", open(os.path.join(path, "magnet")).read())
        else:
            emit("gt", f'/ljcdn/torrent/{id}.torrent')

@app.route("/ljcdn/torrent/<id>.torrent")
def getTorrent(id):
    path = os.path.abspath(f"lt/{id}")
    print(path, os.listdir(path))
    if os.path.exists(path) and len(os.listdir(path)) > 0:
        return send_from_directory(f'lt/{id}', os.listdir(path)[0])
    abort(404)
ses = lt.session()
ses.listen_on(6881, 6891)



def add_torrent(source, id):
    SAVE_PATH  = "/tmp"
    if source.startswith("magnet:?"):
        params = lt.parse_magnet_uri(source)
        params.save_path = SAVE_PATH
        
        print(params)
        handle = ses.add_torrent(params)
    else:
        info = lt.torrent_info(source)
        handle = ses.add_torrent({"ti": info, "save_path": "."})

    info = handle.get_torrent_info()
    while not handle.has_metadata():
        ...
    torrent = Torrent()
    torrent.info_hash = str(info.info_hash())
    torrent.seeders = 0
    torrent.peers = 0
    torrent.t_id = id
    db.session.add(torrent)
    db.session.commit()

def upload_and_torrent(environ, id, current_user: User):
    #with app.request_context(environ):
        socketio.emit("btrack_bgn", (f'Beginning to upload files', id))
        fs = lt.file_storage()
        os.makedirs(os.path.join("torrent_cache", id), exist_ok=True)
        os.makedirs(os.path.join('lt', id))
        for file in request.files.getlist('files'):
            print(file.filename)
            file.save(os.path.join("torrent_cache", id) + "/"+secure_filename(file.filename))
            lt.add_files(fs, os.path.join("torrent_cache", id)+ "/"+secure_filename(file.filename))
            socketio.emit("btrack_bgn", (f'Cached: {file.filename}', id))
        t = lt.create_torrent(fs)
        t.set_creator(request.form.get("creator", current_user.name))
        t.set_comment(request.form.get("comment", ""))
        t.add_tracker(f"http://{ROOT}:6969/announce")
        t.set_priv(False)
        lt.set_piece_hashes(t, os.path.dirname(f'torrent_cache/{id}/.'))
        torrent_data = t.generate()
        with open(f'lt/{id}/{secure_filename(request.form["name"]).replace(" ",".")}.torrent', 'wb+') as f:
            f.write(lt.bencode(torrent_data))
        if request.form.get("tfile_magnet") == "magnet":
            manget_link = lt.make_magnet_uri(lt.torrent_info(f'lt/{id}/{secure_filename(request.form["name"]).replace(" ",".")}.torrent'))
            os.rename(f'lt/{id}/{secure_filename(request.form["name"]).replace(" ",".")}.torrent', f'lt/{id}/magnet')
            with open(f'lt/{id}/magnet', "w+") as f:
                f.write(manget_link)
            add_torrent(manget_link, id)
        else:
            add_torrent(f'lt/{id}/{secure_filename(request.form["name"]).replace(" ",".")}.torrent', id)

        socketio.emit("btrack_done", (f'', id))
import requests

@app.route("/lj-backend/lj-torrentd/tracker")
@login_required
def track():
    r = requests.get(f"http://{ROOT}:6969/stats").json()
    return render_template("tracklist.html", torrents = r)

@app.route("/lj-backend/lj-torrentd/upload", methods=["POST"])
@login_required
def upload_torrent():
    id = ''.join([secrets.choice(string.ascii_letters) for _ in range(30)])
    upload_and_torrent(request.environ.copy(), id, current_user)
    return render_template("torrent_wait.html", id=id)


@app.route("/mitmachen")
def mm():
    if current_user.is_authenticated:
        return redirect("/lj-backend")
    abort(404) 


if __name__ == "__main__":
    socketio.run(app, debug=True)
