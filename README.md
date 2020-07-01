# Kijiji Manager

Kijiji Manager app for viewing, posting, and deleting your Kijiji ads.

Built using the [Flask](https://flask.palletsprojects.com/) framework with Python 3.6+.
Completely API driven, with no web scraping. Runs a local webserver which provides the web user interface.

## Requirements

Kijiji Manager requires Python 3.6+.

#### Minimum dependencies

```
Flask
Flask-WTF
Flask-Login
Flask-Uploads
WTForms
httpx
xmltodict
is-safe-url
phonenumbers
```

## Setup

1. Edit the secret key variable on the first line in [`instance/config.py`](instance/config.py) to a random value
    * To generate a random value you can run the following and copy the output:\
      `python -c "import secrets; print(secrets.token_urlsafe(16))"`
1. Run the app from a shell/terminal: `python run.py`
1. Open a browser and go to http://localhost:5000/ or http://127.0.0.1:5000/
    * Cookies must be enabled in order to log in
1. Login using an existing Kijiji account
    * You must register for a new account on [kijiji.ca](https://www.kijiji.ca/) if you do not yet have one

## Credits

Many of the core architecture concepts have been borrowed from the [Kijiji-Reposter](https://github.com/rybodiddly/Kijiji-Reposter/) project.
Many thanks to [rybodiddly](https://github.com/rybodiddly/) for the work they have done, especially on the Kijiji API.
