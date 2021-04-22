import argparse
import os

from .app import create_app

# Flask app variable used when starting WSGI server
# Get config file argument via environment variable
app = create_app(os.environ.get('CONFIG_FILE', None))


def main():
    """Entry point when module is run from an interactive prompt
    e.g. 'python -m kijiji_manager' or from console script"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='path to config file')
    parser.add_argument('-b', '--bind', help='interface to bind to (default: localhost)')
    parser.add_argument('-p', '--port', type=int, help='port to bind to (default: 5000)')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging')
    args = parser.parse_args()

    app = create_app(args.config)
    app.run(host=args.bind, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
