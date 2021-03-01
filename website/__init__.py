import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth


app = Flask(__name__)
app.config['SECRET_KEY'] = '0e1fb822dfe418183a89f8eac08e6efe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['MSEARCH_INDEX_NAME'] = 'msearch'
app.config['MSEARCH_BACKEND'] = 'whoosh'
app.config['MSEARCH_PRIMARY_KEY'] = 'id'
app.config['MSEARCH_ENABLE'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'basscoder2808@gmail.com'
app.config['MAIL_PASSWORD'] = 'VedantJolly'

print(os.environ.get('EMAIL_USER'))
print(os.environ.get('EMAIL_PASSWORD'))

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='75468103963-2m51dpievr892mnjutmurh9h1j7pod9l.apps.googleusercontent.com',
    client_secret='KnFbhxPe-uUsXsmUwEFIS5v5',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    hd='spit.ac.in',
    # This is only needed if using openId to fetch user info
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)

from website import routes
