from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

zodi_app = Flask(__name__)
zodi_app.config['SECRET_KEY'] = '12549aef8328781a4573d91c6f439141'
zodi_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(zodi_app)    

bcrypt = Bcrypt(zodi_app)

login_manager = LoginManager(zodi_app)
login_manager.login_view = 'login' # function name of the route the ligin required redirects to
login_manager.login_message_category = 'info' # the bootstrap style for the login required message

zodi_app.config['UPLOAD_FOLDER'] = 'uploads'
zodi_app.config['MASKED_FOLDER'] = 'masked_data'
zodi_app.config['PROC_FOLDER'] = 'processed_data'
zodi_app.config['INTERPPED_FOLDER'] = 'interpped_psfs'

from zodi_processing import zodi_routes
