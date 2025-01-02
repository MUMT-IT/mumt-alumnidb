from flask import Blueprint

line_api_blueprint = Blueprint('line_api', __name__, url_prefix='/line-api')

from . import views