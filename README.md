# Kijiji Manager

Kijiji Manager app for viewing, posting, reposting, and deleting your Kijiji ads.

Built using the [Flask](https://flask.palletsprojects.com/) framework with Python 3.6+.
Completely API driven, with no web scraping. Runs a local webserver which provides the web user interface.

Kijiji Manager is able to handle all types of ads under every Kijiji category (although not every ad type has been extensively tested).

If you find any bugs with posting ads, please create a new issue to report it.

## Requirements

Kijiji Manager requires Python 3.6+.

#### Minimum dependencies

* `Flask`
* `Flask-WTF`
* `Flask-Login`
* `Flask-Executor`
* `WTForms`
* `httpx`
* `xmltodict`
* `is-safe-url`
* `phonenumbers`

## Installation

1. Install from source
    1. Clone this repository
       ```
       git clone https://github.com/jackm/kijiji-manager.git
       cd kijiji-manager
       ```
    1. Create a new virtualenv (optional but highly recommended)
       ```
       python -m venv venv
       source venv/bin/activate
       ```
       * If using a virtualenv, you must source the `venv/bin/activate` script each time you start a new shell, otherwise the installed Python packages will not be available
       * If using Windows, the activate script will be at `venv/Scripts/Activate` instead
       * See the Python [virtual environments tutorial](https://docs.python.org/3.6/tutorial/venv.html) for more information
    1. Install the kijiji-manager package from the current directory\
       `pip install .`
1. Copy the sample config file at [`kijiji_manager/kijiji-manager-sample.cfg`](kijiji_manager/kijiji-manager-sample.cfg) and rename it to `kijiji-manager.cfg`, putting it in the instance folder
    * Create a folder named `instance` at the root of this repository if it does not exist
1. Edit the secret key variable on the first line in `instance/kijiji-manager.cfg` to a random value
    * To generate a random value you can run the following and copy the output:\
      `python -c "import secrets; print(secrets.token_urlsafe(16))"`
1. Run the app from a shell/terminal: `python -m kijiji_manager` or `kijiji-manager -c instance/kijiji-manager.cfg`
    * Append `--help` to see all possible command line arguments
1. Open a browser and go to http://localhost:5000/ or http://127.0.0.1:5000/
    * Cookies must be enabled in order to log in
1. Login using an existing Kijiji account
    * You must register for a new account on [kijiji.ca](https://www.kijiji.ca/) if you do not yet have one

For all subsequent runs, start the app again using `python run.py` and then go to the web interface in your browser.
You can also leave the app running in the terminal if you wish.
No background HTTP calls are made unless you refresh or load new pages.

## Screenshots

![Login page](https://user-images.githubusercontent.com/4127823/86979816-3ccf8980-c150-11ea-9b16-1d4a9612ad6b.png)

![Home page](https://user-images.githubusercontent.com/4127823/94874784-dee5d180-0420-11eb-802c-2cb8c55f7bb4.png)

![Show ad page](https://user-images.githubusercontent.com/4127823/86979503-8075c380-c14f-11ea-997b-1ecf84066c2e.png)

![Post ad step 1](https://user-images.githubusercontent.com/4127823/86979508-823f8700-c14f-11ea-963a-4366119303d2.png)

![Post ad step 2](https://user-images.githubusercontent.com/4127823/86979510-8370b400-c14f-11ea-8293-13846c1c8c40.png)

## Credits

Many of the core architecture concepts have been borrowed from the [Kijiji-Reposter](https://github.com/rybodiddly/Kijiji-Reposter/) project.
Many thanks to [rybodiddly](https://github.com/rybodiddly/) for the work they have done, especially on the Kijiji API.
