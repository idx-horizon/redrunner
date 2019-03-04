from flask import Flask
from flask_login import LoginManager
from app.config import Config

app = Flask(__name__, template_folder='../templates', static_url_path='../static')
app.config.from_object(Config)

login = LoginManager(app)
login.login_view = 'login'

THISDB = app.config['REPOSITORY']
APPNAME = app.config['APPNAME']