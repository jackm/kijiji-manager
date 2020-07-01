from flask import session
from flask_login import UserMixin


class User(UserMixin):
    """User model

    Saves user data in Flask session
    """

    def __init__(self, user_id, token, email=None, name=None):
        self.id = user_id
        self.token = token
        self.email = email
        self.name = name

        user_entry = {
            'id': self.id,
            'token': self.token,
            'email': self.email,
            'name': self.name,
        }

        # Create session user db if not already exists
        user_db = session.get('user_db')
        if not user_db:
            session['user_db'] = {}

        # Add user to db if user ID does not yet exist
        if self.id not in session['user_db']:
            session['user_db'].update({self.id: user_entry})

    def is_authenticated(self):
        if 'user_db' not in session:
            return False
        # User authenticated if their ID exists in the user_db dict
        return True if self.id in session['user_db'] else False

    # Get user object if exists, None otherwise
    @classmethod
    def get(cls, user_id):
        if 'user_db' in session:
            if user_id in session['user_db']:
                user = session['user_db'].get(user_id)
                return User(user['id'], user['token'], user['email'], user['name'])

    # Clear current user entry from user db
    @classmethod
    def clear(cls, user_id):
        if 'user_db' in session:
            if user_id in session['user_db']:
                session['user_db'].pop(user_id)
