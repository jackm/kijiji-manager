from flask import Blueprint, flash, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user, login_user, logout_user
from is_safe_url import is_safe_url

from kijiji_manager.models import User
from kijiji_manager.forms.login import LoginForm
from kijiji_manager.forms.conversation import ConversationForm
from kijiji_manager.kijijiapi import KijijiApi, KijijiApiException

user = Blueprint('user', __name__)
kijiji_api = KijijiApi()


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
            user_id, token = kijiji_api.login(email, password)
            display_name = kijiji_api.get_profile(user_id, token)['user:user-profile']['user:user-display-name']
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
    data = kijiji_api.get_profile(current_user.id, current_user.token)
    return render_template('profile.html', data=data)


@user.route('/conversations/<int:page>')
@login_required
def conversations(page):
    data = kijiji_api.get_conversation_page(current_user.id, current_user.token, page)
    return render_template('conversations.html', conversations=data, page=page)


@user.route('/conversation/<uid>', methods=['GET', 'POST'])
@login_required
def conversation(uid):
    data = kijiji_api.get_conversation(current_user.id, current_user.token, uid)
    form = ConversationForm()
    if form.validate_on_submit():
        ad_id = data['user:user-conversation']['user:ad-id']
        owner_id = data['user:user-conversation']['user:ad-owner-id']
        owner_email = data['user:user-conversation']['user:ad-owner-email']
        owner_name = data['user:user-conversation']['user:ad-owner-name']
        replier_id = data['user:user-conversation']['user:ad-replier-id']
        replier_email = data['user:user-conversation']['user:ad-replier-email']
        replier_name = data['user:user-conversation']['user:ad-replier-name']

        # Ad has been deleted if owner ID is 'null'
        # Subject will also say 'Deleted Ad'
        if owner_id != 'null':
            reply_message = form.message.data
            reply_username = None
            reply_email = None
            reply_direction = None

            if owner_id == current_user.id:
                # Replying to our own ad
                reply_email = owner_email
                reply_username = owner_name
                reply_direction = 'buyer'
            elif replier_id == current_user.id:
                # Replying to someone else's ad
                reply_email = replier_email
                reply_username = replier_name
                reply_direction = 'owner'

            kijiji_api.post_conversation_reply(current_user.id, current_user.token, uid, ad_id, reply_username, reply_email, reply_message, reply_direction)
            flash('Reply sent')

            # Redirect to this url, clearing form data and refreshing the page
            return redirect(url_for('.conversation', uid=uid))
        else:
            flash('Ad has been deleted, cannot send reply')

    if form.errors:
        flash(form.errors)
    return render_template('conversation.html', conversation=data, form=form)
