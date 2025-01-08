from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(), unique=True)
    password_hash = db.Column(db.Text())
    active = db.Column(db.Boolean(), default=False, info={'label': 'Is Active?'})
    desc = db.Column(db.Text(), info={'label': 'Description'})

    @property
    def password(self):
        raise AttributeError('Password is not accessible.')

    @password.setter
    def password(self, plain_password):
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        return check_password_hash(self.password_hash, plain_password)