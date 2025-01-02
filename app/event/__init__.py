from flask import Blueprint

event_blueprint = Blueprint('event', __name__, url_prefix='/event')

from . import views