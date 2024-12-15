import os

from flask import Flask
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('://', 'ql://', 1)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app)


from app.main import main_blueprint

app.register_blueprint(main_blueprint)

from app.event import event_blueprint

app.register_blueprint(event_blueprint)

from app.event.models import Event

admin.add_view(ModelView(Event, db.session, category='Event', endpoint='event-admin'))

