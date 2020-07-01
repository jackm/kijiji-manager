from flask import Blueprint, flash, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user, login_user, logout_user
from is_safe_url import is_safe_url

from kijiji_manager.models import User
from kijiji_manager.forms.login import LoginForm
from kijiji_manager.kijijiapi import KijijiApi, KijijiApiException

user = Blueprint('user', __name__)


@user.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        email = request.form['email']
        password = request.form['password']

        # Get user ID, token and user display name from Kijiji
        try:
            user_id, token = KijijiApi().login(email, password)
            display_name = KijijiApi().get_profile(user_id, token)['user:user-profile']['user:user-display-name']
        except KijijiApiException as e:
            flash(e)
            return render_template('login.html', form=form)

        # Create user object instance and login
        login_user(User(user_id, token, email, display_name))

        # Validate the `next` parameter
        next = request.values.get('next')
        if next and not is_safe_url(next, request.host_url):
            return abort(400)

        # Redirect to home on successful login
        flash('Logged in')
        return redirect(next or url_for('main.home'))

    if form.errors:
        flash(form.errors)
    return render_template('login.html', form=form)


@user.route('/logout')
@login_required
def logout():
    User.clear(current_user.id)
    logout_user()
    flash('Logged out')
    return redirect(url_for('.login'))


@user.route('/profile')
@login_required
def profile():
    data = KijijiApi().get_profile(current_user.id, current_user.token)
    return render_template('profile.html', data=data)
