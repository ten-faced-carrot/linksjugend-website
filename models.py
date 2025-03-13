from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db = SQLAlchemy()

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


class Pad(db.Model):
    _id         = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    info_hash   = db.Column(db.VARCHAR(120))
    content     = db.Column(db.Text)
    date = db.Column(db.DATETIME)

    

class Blogeintrag(db.Model):
    __tablename__ = 'blogeintrag'
    _id = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    date = db.Column(db.DATETIME)
    body = db.Column(db.VARCHAR(10240))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Magnet(db.Model):
    _id = db.Column("id", db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(120))
    hash = db.Column(db.VARCHAR(120))
    link = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
