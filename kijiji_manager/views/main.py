import math
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from kijiji_manager.kijijiapi import KijijiApi

main = Blueprint('main', __name__)
kijiji_api = KijijiApi()


@main.route('/')
def index():
    """Redirect to appropriate page depending on if user is currently logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('.home'))
    else:
        return redirect(url_for('user.login'))


@main.route('/home')
@login_required
def home():
    """Show home page."""
    data = kijiji_api.get_ad(current_user.id, current_user.token)
    return render_template('home.html', name=current_user.name, data=data)


@main.app_template_filter('islist')
def islist(data):
    """Return true if value is a list object."""
    return isinstance(data, list)


@main.app_template_filter('datetime')
def format_datetime(date, fmt=None):
    """Convert datetime string to datetime object.
    datetime object will get converted back to a string via __repr__() when rendered in a template.
    Kijiji API returns datetime strings in full ISO 8601 format; e.g. '2020-06-20T20:57:42.000Z'.
    """
    if fmt is None:
        fmt = '%Y-%m-%dT%H:%M:%S.%f'

    try:
        date = date.replace('Z', '')  # Strip out trailing zone designator if present
        return datetime.strptime(date, fmt)
    except (ValueError, AttributeError):
        return None


@main.app_template_filter('imgthumbs')
def get_img_thumbs(data):
    """Get list of thumbnail image urls."""
    try:
        pics = data['pic:pictures']['pic:picture']
    except (TypeError, KeyError):
        # No images in ad
        return [None]

    # 'pics' is either a list of dicts, or a single dict if there is only one ad image
    # Force it to be a list in order to loop through it
    if not isinstance(pics, list):
        pics = [pics]

    urls = []
    for pic in pics:
        # Multiple sizes per image
        for size in pic['pic:link']:
            # Only return thumbnail url
            if size['@rel'] == 'thumbnail':
                urls.append(size['@href'])
    return urls


@main.app_template_filter('imgthumbfirst')
def get_img_thumb_first(data):
    """Get first thumbnail image url."""
    return get_img_thumbs(data)[0]


@main.app_template_filter('adurl')
def get_ad_url(data):
    """Get public website ad url."""
    try:
        links = data['ad:link']
    except (TypeError, KeyError):
        # No url in ad
        return None

    for link in links:
        if link['@rel'] == 'self-public-website':
            return link['@href']


@main.app_template_filter('adpage')
def get_ad_page_number(data):
    """Convert ad rank to page number."""
    try:
        return int(math.ceil(int(data) / 20))
    except (TypeError, ValueError):
        return None
