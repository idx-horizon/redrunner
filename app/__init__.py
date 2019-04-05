from flask import Flask
from flask_login import LoginManager
from app.config import Config

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap


app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)
 

bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'


THISDB = app.config['REPOSITORY']
APPNAME = app.config['APPNAME']
THISCONFIG = app.config

flaskdb = SQLAlchemy(app)
migrate = Migrate(app, flaskdb)

from app import models
