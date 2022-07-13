import os

from flask import Flask, flash, redirect, url_for, request, render_template
from flask_login import LoginManager
from werkzeug.serving import WSGIRequestHandler

from . import __version__ as app_version
from .kijijiapi import KijijiApiException
from .models import User


def create_app(config=None):

    # Use HTTP/1.1
    # Shouldn't be strictly necessary but it has some extra niceties such as automatic keepalive
    WSGIRequestHandler.protocol_version = "HTTP/1.1"

    app = Flask(__name__, instance_relative_config=True)

    config_name = 'kijiji-manager.cfg'

    if config:
        config_path = os.path.abspath(config)
    else:
        # Load from `instance` folder
        config_path = config_name

    try:
        app.config.from_pyfile(config_path)
    except FileNotFoundError:
        config_sample = os.path.join(os.path.dirname(__file__), 'kijiji-manager-sample.cfg')
        print("Unable to load your config file.\n"
              f"Either specify one with the `-c` flag, or put one named '{config_name}' in the Flask instance folder at the path below.\n"
              "You may have to create the instance folder if it doesn't already exist.\n")
        print(f"Sample config: {config_sample}")
        print(f"Instance folder: {app.instance_path}")
        raise

    # Favicon route rule
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

    # Handle KijijiApi exceptions
    # Print error message rather than showing a generic 500 Internal Server Error
    @app.errorhandler(KijijiApiException)
    def handle_exceptions(e):
        return render_template('error.html', message=e)

    # Inject app version to all templates
    @app.context_processor
    def inject_version():
        return dict(app_version=app_version)

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
