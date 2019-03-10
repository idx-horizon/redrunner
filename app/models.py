
from datetime import datetime
from app import flaskdb, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Apple(flaskdb.Model):
    xid     = flaskdb.Column(flaskdb.Integer, primary_key=True)
    xname   = flaskdb.Column(flaskdb.String(64), index=True, unique=True)


class Runner(flaskdb.Model):
    rid = flaskdb.Column(flaskdb.String(10), index=True, unique=True, primary_key=True)
    public_flag = flaskdb.Column(flaskdb.Boolean)
    fullname = flaskdb.Column(flaskdb.String(50))
    threshold = flaskdb.Column(flaskdb.String(10))
    
    def __repr__(self):
        return '<Runner {} {}'.format(self.rid, self.fullname) 
    
class User(UserMixin, flaskdb.Model):
    id            = flaskdb.Column(flaskdb.Integer, primary_key=True)
    username      = flaskdb.Column(flaskdb.String(64), index=True, unique=True)
    rid           = flaskdb.Column(flaskdb.String(10), index=True, unique=True)
    email         = flaskdb.Column(flaskdb.String(120), index=True, unique=True)
    password_hash = flaskdb.Column(flaskdb.String(128))

    def __repr__(self):
        return '<User {} {}>'.format(self.username, self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
    
    