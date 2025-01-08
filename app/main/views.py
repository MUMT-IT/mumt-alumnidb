import os

import requests
from flask import render_template, request, url_for, session, redirect, jsonify
from flask_login import login_user, current_user, logout_user

from app.main.models import User
from app.main import main_blueprint as main
from app.main.forms import LoginForm


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(request.args.get('next') or url_for('event.all_events'))
        else:
            return 'Invalid username or password.'
    return render_template('main/login_form.html', form=form)


@main.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(request.args.get('next') or url_for('main.login'))
    return redirect(url_for('main.logout'))
