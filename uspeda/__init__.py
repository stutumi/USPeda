from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.bcrypt import Bcrypt

app = Flask(__name__)
app.debug = True
app.config.from_object('config')

db = SQLAlchemy(app)
mail = Mail(app)
bcrypt = Bcrypt(app)

from uspeda.models import cache_all_users
cache_all_users()

from uspeda import views
