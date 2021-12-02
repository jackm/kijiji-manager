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
       python3 -m venv venv
       source venv/bin/activate
       ```
       * When using a virtualenv, you must source the `venv/bin/activate` script each time you start a new shell, otherwise the installed Python packages will not be available
       * If using a Debian based Linux distro, and the _venv_ Python library is not found or if there is an error about missing _ensurepip_, you will have to apt install `python3-venv` first
       * If using Windows, you may have to use the `py` command in place of `python` or `python3`
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

For all subsequent runs, start the app again using `python -m kijiji_manager` or `kijiji-manager -c instance/kijiji-manager.cfg` and then go to the web interface in your browser.
You can also leave the app running in the terminal if you wish.
No background HTTP calls are made unless you refresh or load new pages.

## Command line arguments

```bash
usage: kijiji-manager [-h] [-c CONFIG] [-b BIND] [-p PORT] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config file
  -b BIND, --bind BIND  interface to bind to (default: localhost)
  -p PORT, --port PORT  port to bind to (default: 5000)
  -d, --debug           enable debugging
```

## Default form values

Default values for certain form fields can be chosen by adding any of the following variables to their `instance/kijiji-manager.cfg` config file:

* `DEFAULT_AD_TITLE`
* `DEFAULT_AD_DESCRIPTION`
* `DEFAULT_AD_PRICE`
* `DEFAULT_POSTAL_CODE`
* `DEFAULT_PHONE`
* `DEFAULT_LOCATION2_CONTAINS`
  * Select second location tier by checking if location label contains given string value; case-insensitive
* `DEFAULT_LOCATION3_CONTAINS`
  * Select third location tier (if required) by checking if location label contains given string value; case-insensitive

Note that these config values are only read once during startup - you will need to restart the app for any changes to take effect.

e.g.

```
DEFAULT_AD_TITLE = 'This is a test ad title'
DEFAULT_AD_DESCRIPTION = 'This is a test ad description'
DEFAULT_AD_PRICE = 149.99
DEFAULT_POSTAL_CODE = 'A1A 1A1'
DEFAULT_PHONE = '555-5555'
DEFAULT_LOCATION2_CONTAINS = 'Toronto'
DEFAULT_LOCATION3_CONTAINS = 'Markham'
```

## Docker container

A [Dockerfile](Dockerfile) is provided as well as a [docker-compose.yml](docker-compose.yml) file to allow running this app within a [Docker](https://docs.docker.com/) container.
At minimum this method will require [Docker to be installed](https://docs.docker.com/get-docker/).

Using this method does not require installing any Python packages locally - the whole app will be installed and run within an isolated container.

You should still create a `instance/kijiji-manager.cfg` file containing a randomly generated secret key within the instance folder (steps 2 and 3 of _Installation_).
By default, the web interface will still be reachable at http://localhost:5000/ or http://127.0.0.1:5000/.

If you want to provide a custom config file path other than `instance/kijiji-manager.cfg`, this can be done by setting the `CONFIG_FILE` environment variable when running the container.

### Docker Compose

Docker Compose is an additional tool that can be used to easily deploy app containers.
In this case, Docker Compose is used to automatically build and run the app container. 

Run `docker-compose up` from the root of this repository.

If changes are made to the _kijiji_manager_ package, you will have to run `docker-compose up --build` instead to force rebuild the container image.

### Without Docker Compose

If you do not want to use Docker Compose, you can build the container image and then run the container using the following commands from the root of this repository:

```
docker build -t kijiji-manager .
docker run --rm --name kijiji-manager -p 5000:80 -v "$(pwd)"/instance:/app/instance kijiji-manager
```

Append the `--detach` option to the `docker run` command to run the container in the background (detached mode).

## Screenshots

![Login page](https://user-images.githubusercontent.com/4127823/86979816-3ccf8980-c150-11ea-9b16-1d4a9612ad6b.png)

![Home page](https://user-images.githubusercontent.com/4127823/94874784-dee5d180-0420-11eb-802c-2cb8c55f7bb4.png)

![Show ad page](https://user-images.githubusercontent.com/4127823/86979503-8075c380-c14f-11ea-997b-1ecf84066c2e.png)

![Post ad step 1](https://user-images.githubusercontent.com/4127823/86979508-823f8700-c14f-11ea-963a-4366119303d2.png)

![Post ad step 2](https://user-images.githubusercontent.com/4127823/86979510-8370b400-c14f-11ea-8293-13846c1c8c40.png)

## Credits

Many of the core architecture concepts have been borrowed from the [Kijiji-Reposter](https://github.com/rybodiddly/Kijiji-Reposter/) project.
Many thanks to [rybodiddly](https://github.com/rybodiddly/) for the work they have done, especially on the Kijiji API.
