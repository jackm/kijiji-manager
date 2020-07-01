import os
from xml.parsers.expat import ExpatError, errors

import xmltodict
from flask import current_app


def _parse_xml(file, mode='r'):
    with open(file, mode=mode, encoding='utf-8') as f:
        contents = f.read()
        try:
            return xmltodict.parse(contents)
        except ExpatError as e:
            error_msg = errors.messages[e.code]
            raise


def get_category_data():
    return _parse_xml(os.path.join(current_app.static_folder, 'categories.xml'))


def get_location_data():
    return _parse_xml(os.path.join(current_app.static_folder, 'locations.xml'))


def get_attrib(attrib_id):
    attrib_file = os.path.join(current_app.static_folder, 'attributes', attrib_id)
    if os.path.isfile(attrib_file):
        return _parse_xml(attrib_file)
