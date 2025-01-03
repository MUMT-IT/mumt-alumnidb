import os

import requests
from flask import render_template, request, url_for, session, redirect, jsonify

from app.main import main_blueprint as main


@main.route('/')
def index():
    return render_template('main/index.html')
