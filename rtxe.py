from flask import Blueprint as Flask, current_app, render_template, request, redirect
import random, string
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from string import ascii_letters, digits
from models import Pad, db
from datetime import datetime

app = Flask(__name__, "pad_helper")

documents = {}
users = {}  # Speichert Nutzer (socket_id -> Name)

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

@socketio.on("join")
def handle_join(data):
    users[request.sid] = {
        "name": data["name"],
        "color": random_color()
    }
    emit("user_list", users, broadcast=True)

@socketio.on("join")
def handle_join(data):
    users[request.sid] = data["name"]
    data["content"] = documents[data["id"]]["content"]
    emit("user_list", list(users.values()), broadcast=True)
    emit("update", data, broadcast=True)


@socketio.on("save")
def handle_save(data):
    pd = Pad.query.filter_by(info_hash=data["id"]).first()
    if not pd:
        pd = Pad(info_hash=data["id"])
        db.session.add(pd)
    pd.name = data["name"]
    pd.content = data["content"]
    pd.date = datetime.now()
    db.session.commit()
    
    emit("update", data, broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    users.pop(request.sid, None)
    emit("user_list", list(users.values()), broadcast=True)

@socketio.on("update")
def handle_update(data):
    global document
    documents[data["id"]]["content"] = data["content"]
    emit("update", data, broadcast=True)

@app.route("/<id>")
def index(id):
    if id not in documents:
        documents[id] = {"content": ""}
    return render_template("editor.html", id=id)

@app.route("/")
def root():
    return redirect("/" + ''.join(random.choices(ascii_letters+digits, k=20)))

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0")
