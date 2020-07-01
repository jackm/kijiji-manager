from flask import Blueprint, request, jsonify

from kijiji_manager.common import get_category_data, get_location_data, get_attrib

json = Blueprint('json', __name__)


# Return JSON list of subcategories under given category ID
# Each subcategory is a dict with category 'id' and 'name' keys
#
# Returns an empty list if no subcategories exist under the given category ID,
# or given category ID(s) are not found
@json.route('/cat')
def get_category():
    # Start at category ID 0 ('All Categories')
    data = get_category_data()['cat:categories']['cat:category']

    # Top level categories
    categories = _get_subcategories(data)

    # Get category IDs from query string
    category1 = request.args.get('category1')
    category2 = request.args.get('category2')

    if category1:
        # Subcategories of top level
        for cat in categories:
            if cat['@id'] == category1:
                categories = _get_subcategories(cat)
                break

        if category2:
            # Subcategories of second level
            for cat in categories:
                if cat['@id'] == category2:
                    categories = _get_subcategories(cat)
                    break

    return jsonify([{'id': c['@id'], 'name': c['cat:id-name']} for c in categories])


# Return list of subcategories under given category dict
def _get_subcategories(data):
    cat_list = []
    try:
        if int(data['cat:children-count']) > 0:
            cat_list = data['cat:category']
    except (KeyError, TypeError):
        pass
    return cat_list


# Return JSON list of sublocations under given location ID
# Each sublocation is a dict with location 'id', 'name', 'long', and 'lat' keys
#
# Returns an empty list if no sublocations exist under the given location ID,
# or given location ID(s) are not found
@json.route('/loc')
def get_location():
    # Start at location ID 0 ('Canada')
    data = get_location_data()['loc:locations']['loc:location']

    locations = data['loc:location']

    # Get location IDs from query string
    location1 = request.args.get('location1')
    location2 = request.args.get('location2')

    if location1:
        # Sublocations of top level
        for loc in locations:
            if loc['@id'] == location1:
                locations = loc.get('loc:location', [])
                break

        if location2:
            # Sublocations of second level
            for loc in locations:
                if loc['@id'] == location2:
                    locations = loc.get('loc:location', [])
                    break

    return jsonify([{
        'id': l['@id'],
        'name': l['loc:localized-name'],
        'long': l['loc:longitude'],
        'lat': l['loc:latitude'],
    } for l in locations])


# Return JSON list of supported values for each dependent attributes for a given attribute ID
# Each supported value is a dict with supported value 'id' and 'name' keys
#
# Returns an empty list if no dependent attributes exist under the given attribute ID,
# or given attribute ID is not found
@json.route('/attrib')
def get_supported_values():
    # Get parameters from query string
    attrib_id = request.args.get('attrib')
    value = request.args.get('value')

    attribs = []
    if attrib_id:
        data = get_attrib(attrib_id)
        if data:
            if 'attr:dependent-attributes' in data['ad:ad']:
                # Start at list of all dependent attributes
                data = data['ad:ad']['attr:dependent-attributes']['attr:dependent-attribute']['attr:dependent-supported-value']

                if value:
                    for attr in data:
                        if attr['attr:supported-value']['#text'] == value:
                            # Supported subvalues
                            for subval in attr['attr:dependent-attribute']['attr:supported-value']:
                                attribs.append({'id': subval['#text'], 'name': subval['@localized-label']})

    return jsonify(attribs)
