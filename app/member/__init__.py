from flask import Blueprint

member_blueprint = Blueprint('member', __name__, url_prefix='/member')

from . import views