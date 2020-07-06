from flask import Flask, flash, redirect, url_for, request
from flask_login import LoginManager

from .models import User


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile('config.py')
    app.add_url_rule('/favicon.ico', 'favicon', lambda: app.send_static_file('favicon.ico'))

    # Trim newlines and leading whitespace around template tags
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # Suppress "None" output as string
    app.jinja_env.finalize = lambda x: x if x is not None else ''

    # Flask-Executor
    from .views.ad import executor as ad_executor
    ad_executor.init_app(app)

    # Blueprints
    from .views.main import main
    from .views.user import user
    from .views.ad import ad
    from .views.json import json
    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(ad)
    app.register_blueprint(json)

    # Flask-Login
    login_manager = LoginManager()

    @login_manager.unauthorized_handler
    def unauthorized():
        flash('Please log in to access this page.')
        next = url_for(request.endpoint, **request.view_args)
        return redirect(url_for('user.login', next=next))

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    login_manager.init_app(app)

    return app
