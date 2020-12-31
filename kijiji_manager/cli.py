import argparse

from kijiji_manager import create_app


def run():
    """Run Kijiji Manager Flask app"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='path to config file')
    parser.add_argument('-b', '--bind', help='interface to bind to (default: localhost)')
    parser.add_argument('-p', '--port', type=int, help='port to bind to (default: 5000)')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging')
    args = parser.parse_args()

    app = create_app(args.config)
    app.run(host=args.bind, port=args.port, debug=args.debug)
