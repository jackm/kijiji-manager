import os
from datetime import datetime
from time import sleep

import xmltodict
from flask import Blueprint, flash, render_template, redirect, url_for, session, current_app, request
from flask_executor import Executor
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, DateField, SelectMultipleField, widgets
from wtforms.validators import InputRequired, Optional

from kijiji_manager.forms.post import CategoryForm, PostForm, PostManualForm
from kijiji_manager.kijijiapi import KijijiApi

ad = Blueprint('ad', __name__)
kijiji_api = KijijiApi()
executor = Executor()


@ad.route('/ad/<ad_id>')
@login_required
def show(ad_id):
    data = kijiji_api.get_ad(current_user.id, current_user.token, ad_id)
    return render_template('ad.html', data=data)


@ad.route('/delete/<ad_id>')
@login_required
def delete(ad_id):
    kijiji_api.delete_ad(current_user.id, current_user.token, ad_id)
    flash(f'Deleted ad {ad_id}')
    return redirect(url_for('main.home'))


@ad.route('/post_manual', methods=['GET', 'POST'])
@login_required
def post_manual():
    form = PostManualForm()
    if form.validate_on_submit():
        if form.file.data:
            xml_payload = form.file.data.read()

            ad_id = kijiji_api.post_ad(current_user.id, current_user.token, xml_payload)
            flash(f'Manually posted ad {ad_id}')

            # Save ad payload
            user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            ad_file = os.path.join(user_dir, f'{ad_id}.xml')
            with open(ad_file, 'w', encoding='utf-8') as f:
                if isinstance(xml_payload, bytes):
                    xml_payload = xml_payload.decode('utf-8')
                f.write(xml_payload)
            flash(f'Ad {ad_id} payload saved to {ad_file}')

    if form.errors:
        flash(form.errors)
    return render_template('post_manual.html', form=form)


@ad.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    # Multi-step form
    step = [
        'choose_category',
        'fill_attributes',
        'submit',
    ]

    category_form = CategoryForm()
    category_form.cat1.choices = [(cat['@id'], cat['cat:id-name']) for cat in kijiji_api.get_categories(current_user.id, current_user.token)['cat:categories']['cat:category']['cat:category']]

    form = PostForm()

    if 'step' not in request.form:
        # Step 1: Choose ad category

        return render_template('post.html', form=category_form, step=step[0], next_step=step[1])

    elif request.form['step'] == step[1]:
        # Step 2: Fill in ad attributes

        if not category_form.validate_on_submit():
            flash(category_form.errors)
            return redirect(url_for('.post'))

        # Get most significant category ID from given set of categories in previous step form
        category_choice = (lambda x1, x2, x3: x3 if x3 else x2 if x2 else x1)(category_form.cat1.data, category_form.cat2.data, category_form.cat3.data)
        session['category'] = category_choice
        data = kijiji_api.get_attributes(current_user.id, current_user.token, category_choice)

        # Update supported ad type choices
        try:
            form.adtype.choices = [(x['#text'], x['@localized-label']) for x in data['ad:ad']['ad:ad-type']['ad:supported-value']]
            session['adtype.choices'] = form.adtype.choices
        except KeyError:
            flash('No supported ad types available')

        # Location options
        locations = kijiji_api.get_locations(current_user.id, current_user.token)
        try:
            location_list = [(loc['@id'], loc['loc:localized-name']) for loc in locations['loc:locations']['loc:location']['loc:location']]
        except KeyError:
            # Only one location
            location_list = locations['loc:locations']['loc:location']['loc:localized-name']
        form.loc1.choices = location_list
        session['loc1.choices'] = form.loc1.choices

        # Default form values from config file
        default_ad_title = current_app.config.get('DEFAULT_AD_TITLE')
        default_ad_desc = current_app.config.get('DEFAULT_AD_DESCRIPTION')
        default_ad_price = current_app.config.get('DEFAULT_AD_PRICE')
        default_postalcode = current_app.config.get('DEFAULT_POSTAL_CODE')
        default_fulladdress = current_app.config.get('DEFAULT_FULL_ADDRESS')
        default_phone = current_app.config.get('DEFAULT_PHONE')
        try:
            # Only apply default values if one was given
            if default_ad_title:
                form.adtitle.data = str(default_ad_title)
            if default_ad_desc:
                form.description.data = str(default_ad_desc)
            if default_ad_price:
                form.price.data = float(default_ad_price)
            if default_postalcode:
                form.postalcode.data = str(default_postalcode)
            if default_fulladdress:
                form.fulladdress.data = str(default_fulladdress)
            if default_phone:
                form.phone.data = str(default_phone)
        except (TypeError, ValueError) as e:
            flash(f'Unable to parse value from config file: {e}')

        # Begin parsing attributes xml for selected category
        attrib_types = {
            'enums': [],
            'strings': [],
            'integers': [],
            'dates': [],
            'bools': [],
            'excepts': [],
        }
        if 'attr:attribute' in data['ad:ad']['attr:attributes']:
            attribs = data['ad:ad']['attr:attributes']['attr:attribute']
            try:
                # Force to list if only one value
                if not isinstance(attribs, list):
                    attribs = [attribs]

                for attrib in attribs:
                    # Attribute has not been deprecated and is write supported (i.e. able to post to ad)
                    if attrib['@deprecated'] == 'false' and attrib['@write'] != 'unsupported':
                        item = {
                            'label': {attrib['@name']: attrib['@localized-label']},
                            'required': attrib['@write'] == 'required',  # Record if attribute is required or optional
                            'sub-type': attrib.get('@sub-type', None),  # Some attributes have a sub-type
                        }

                        if attrib['@type'] == 'ENUM':
                            item.update({'choices': {}})
                            if 'attr:supported-value' in attrib:
                                values = attrib['attr:supported-value']

                                # Force to list if only one value
                                if not isinstance(values, list):
                                    values = [values]

                                for value in values:
                                    item['choices'].update({value['#text']: value['@localized-label']})
                            attrib_types['enums'].append(item)

                        if attrib['@type'] == 'STRING':
                            attrib_types['strings'].append(item)

                        if attrib['@type'] == 'INTEGER':
                            attrib_types['integers'].append(item)

                        if attrib['@type'] == 'DATE':
                            attrib_types['dates'].append(item)

                        if attrib['@type'] == 'BOOLEAN':
                            attrib_types['bools'].append(item)
            except KeyError:
                flash('No standard attributes found, attempting defaults')
                # Attempt default parsing
                # Assume ENUM type
                name = ''
                label = ''
                for key, value in data['ad:ad']['attr:attributes']['attr:attribute'].items():
                    if key == '@localized-label':
                        label = value
                    if key == '@name':
                        name = value
                    if key == 'attr:supported-value':
                        item = {
                            'label': {name: label},
                            'choices': {},
                        }
                        for item in value:
                            item['choices'].update({item['#text']: item['@localized-label']})

                        attrib_types['excepts'].append(item)

        # Build dynamic attributes form
        attrib_form = create_attribute_form(attrib_types)
        session['attrib_types'] = attrib_types

        return render_template('post.html', form=form, step=step[1], next_step=step[2], attrib_form=attrib_form, attrib=category_choice)

    elif request.form['step'] == step[2]:
        # Restore dynamic form data
        if not form.adtype.choices:
            form.adtype.choices = session.get('adtype.choices', [])
        if not form.loc1.choices:
            form.loc1.choices = session.get('loc1.choices', [])
        attrib_form = create_attribute_form(session.get('attrib_types'))

        # Update dynamic car or motorcycle model choices
        if hasattr(attrib_form, 'carmake') and hasattr(attrib_form, 'carmodel'):
            attrib_form.carmodel.choices = get_vehicle_model_choices(session.get('category'), attrib_form.carmake.data)
        if hasattr(attrib_form, 'motorcyclesmake') and hasattr(attrib_form, 'motorcyclesmodel'):
            attrib_form.motorcyclesmodel.choices = get_vehicle_model_choices(session.get('category'), attrib_form.motorcyclesmake.data)

        if not form.validate_on_submit() or not attrib_form.validate_on_submit():
            if form.errors:
                flash(form.errors)
            if attrib_form.errors:
                flash(attrib_form.errors)
            return render_template('post.html', form=form, step=step[1], next_step=step[2], attrib_form=attrib_form, attrib=session.get('category'))

        # Get most significant location ID from given set of locations in previous step form
        # Default to 'Canada' => '0' if none given
        location_choice = (lambda x1, x2, x3: x3 if x3 else x2 if x2 else x1 if x1 else '0')(form.loc1.data, form.loc2.data, form.loc3.data)

        # Generate Geo Location Data
        location = kijiji_api.geo_location(form.postalcode.data)

        # Begin assembling entire payload
        # All of the keys in the following dict are always present in every ad post payload,
        # however some may be left empty if not used
        payload = {
            'ad:ad': {
                '@xmlns:ad': 'http://www.ebayclassifiedsgroup.com/schema/ad/v1',
                '@xmlns:cat': 'http://www.ebayclassifiedsgroup.com/schema/category/v1',
                '@xmlns:loc': 'http://www.ebayclassifiedsgroup.com/schema/location/v1',
                '@xmlns:attr': 'http://www.ebayclassifiedsgroup.com/schema/attribute/v1',
                '@xmlns:types': 'http://www.ebayclassifiedsgroup.com/schema/types/v1',
                '@xmlns:pic': 'http://www.ebayclassifiedsgroup.com/schema/picture/v1',
                '@xmlns:vid': 'http://www.ebayclassifiedsgroup.com/schema/video/v1',
                '@xmlns:user': 'http://www.ebayclassifiedsgroup.com/schema/user/v1',
                '@xmlns:feature': 'http://www.ebayclassifiedsgroup.com/schema/feature/v1',
                '@id': '',
                'cat:category': {'@id': session['category']},
                'loc:locations': {'loc:location': {'@id': location_choice}},
                'ad:ad-type': {'ad:value': form.adtype.data},
                'ad:title': form.adtitle.data,
                'ad:description': form.description.data,
                'ad:price': {'types:price-type': {'types:value': form.pricetype.data}},
                'ad:account-id': current_user.id,
                'ad:email': current_user.email,
                'ad:poster-contact-email': current_user.email,
                # 'ad:poster-contact-name': None,  # Not sent by Kijiji app
                'ad:phone': form.phone.data,
                'ad:ad-address': {
                    'types:radius': 400,
                    'types:latitude': location.latitude,
                    'types:longitude': location.longitude,
                    'types:full-address': form.fulladdress.data,
                    'types:zip-code': form.postalcode.data,
                },
                'ad:visible-on-map': 'true',  # appears to make no difference if set to 'true' or 'false'
                'attr:attributes': create_attribute_payload(attrib_form.data),
                'pic:pictures': create_picture_payload(form.data),
                'vid:videos': None,
                'ad:adSlots': None,
                'ad:listing-tags': None,
            }
        }

        # Set price if dollar amount given
        if form.price.data:
            payload['ad:ad']['ad:price'].update({
                'types:amount': form.price.data,
                'types:currency-iso-code': {'types:value': 'CAD'},  # Assume Canadian dollars
            })

        xml_payload = xmltodict.unparse(payload, short_empty_elements=True)

        # Submit final payload
        ad_id = kijiji_api.post_ad(current_user.id, current_user.token, xml_payload)
        flash(f'Ad {ad_id} posted!')

        # Save ad payload
        user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        ad_file = os.path.join(user_dir, f'{ad_id}.xml')
        with open(ad_file, 'w', encoding='utf-8') as f:
            f.write(xml_payload)
        flash(f'Ad {ad_id} payload saved to {ad_file}')

        return redirect(url_for('main.home'))


class MultiCheckboxField(SelectMultipleField):
    """A multiple-select, except displays a list of checkboxes"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class KijijiDateField(DateField):
    """A date field, except appends a time to the value after"""
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        if self.data:
            # Append static time to date value
            # Kijiji date values expected to be a datetime string in ISO 8601 format but the time portion is not actually used
            self.data = datetime.combine(self.data, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%SZ')


# Build dynamic attribute form
def create_attribute_form(types):
    # Insert field attribute to form object
    def insert_attr(obj, field_type, data, **kwargs):
        try:
            for field_id, title in data['label'].items():
                validators = []

                if 'required' in data:
                    validators.append(InputRequired() if data['required'] else Optional())

                if field_type == SelectField:

                    # Use multi-checkbox field when sub-type is multi-valued
                    if data['sub-type'] == 'MULTI_VALUED':
                        field_type = MultiCheckboxField

                    choices = [c for c in data['choices'].items()]
                    setattr(obj, field_id, field_type(title, validators=validators, choices=choices, **kwargs))
                else:
                    setattr(obj, field_id, field_type(title, validators=validators, **kwargs))
        except KeyError:
            pass

    class AttributeForm(FlaskForm):
        class Meta:
            csrf = False

    if isinstance(types, dict):
        for item in types.get('enums', []):
            insert_attr(AttributeForm, SelectField, item)

        for item in types.get('strings', []):
            insert_attr(AttributeForm, StringField, item)

        for item in types.get('integers', []):
            insert_attr(AttributeForm, IntegerField, item)

        for item in types.get('dates', []):
            insert_attr(AttributeForm, KijijiDateField, item, render_kw={'placeholder': 'YYYY-MM-DD'})

        for item in types.get('bools', []):
            insert_attr(AttributeForm, BooleanField, item)

        # Create attributes for anything caught by exceptions during attributes xml parsing, assuming enum type
        for item in types['excepts']:
            insert_attr(AttributeForm, SelectField, item)

    return AttributeForm()


# Get dynamic car or motorcycle model choices
# Return choices as list of tuples
def get_vehicle_model_choices(attrib_id, value):
    choices = []
    data = kijiji_api.get_attributes(current_user.id, current_user.token, attrib_id)
    if data:
        if 'attr:dependent-attributes' in data['ad:ad']:
            # Start at list of all dependent attributes
            data = data['ad:ad']['attr:dependent-attributes']['attr:dependent-attribute']['attr:dependent-supported-value']

            if value:
                for attr in data:
                    if attr['attr:supported-value']['#text'] == value:
                        # Supported subvalues
                        for subval in attr['attr:dependent-attribute']['attr:supported-value']:
                            choices.append((subval['#text'], subval['@localized-label']))
    return choices


# Build attributes payload dict
def create_attribute_payload(data):
    def isnumber(x):
        try:
            float(x)
            return True
        except (TypeError, ValueError):
            return False

    payload = {'attr:attribute': []}
    for key, value in data.items():
        # Skip empty attributes, except numbers which could be falsy
        if not value and not isnumber(value):
            continue

        # Boolean attributes must be a string of 'true' or 'false'
        if value is True or value == 'y':
            value = 'true'
        elif value is False or value == 'n':
            value = 'false'

        # Multi-valued attributes are lists
        if isinstance(value, list):
            # Convert to string of comma-separated values
            value = ','.join(value)

        payload['attr:attribute'].append({
            # '@type': '',  # Not sent by Kijiji app
            '@localized-label': '',
            '@name': key,
            'attr:value': value,
        })
    return payload if len(payload['attr:attribute']) else {}


# Build picture payload dict from file* fields
@login_required
def create_picture_payload(data):
    payload = {'pic:picture': []}

    # Mapping of image size names to size in px
    image_sizes = {
        'extraLarge': 800,
        'large': 500,
        'normal': 400,
        'thumbnail': 64,
    }

    for key, value in data.items():
        if key.startswith('file') and value:
            link = kijiji_api.upload_image(current_user.id, current_user.token, value)

            # Add a separate link for each image size
            links = []
            for size_name, size_px in image_sizes.items():
                links.append({
                    '@rel': size_name,
                    '@href': f'{link}?rule=kijijica-{size_px}-jpg',
                })

            payload['pic:picture'].append({'pic:link': links})

    return payload if len(payload['pic:picture']) else {}


@ad.route('/repost/<ad_id>')
@login_required
def repost(ad_id):
    # Get existing ad
    user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)
    ad_file = os.path.join(user_dir, f'{ad_id}.xml')

    if not os.path.isfile(ad_file):
        flash(f'Cannot repost, ad file {ad_file} does not exist')
        return redirect(url_for('main.home'))

    with open(ad_file, 'r', encoding='utf-8') as f:
        xml_payload = f.read()

    # Kijiji changed their image upload API on around 2022-06-27 to use a different image host. Ad payloads that
    # still contain the old image host URLs will be rejected unless the URLs are translated to the new image host.
    # For ad payloads that already use the new image host, this translation should have no effect.
    xml_payload = translate_image_urls(ad_id, xml_payload)

    # Delete existing ad
    kijiji_api.delete_ad(current_user.id, current_user.token, ad_id)
    flash(f'Deleted old ad {ad_id}')

    # Waiting for 3 minutes appears to be enough time for Kijiji to not consider it a duplicate ad
    delay_minutes = 3

    # Delay and then run callback to post ad again
    future_response = executor.submit(delay, delay_minutes * 60, {'payload': xml_payload, 'ad_id': ad_id})
    future_response.add_done_callback(post_ad_again)

    flash(f'Reposting ad in background after {delay_minutes} minute delay... Do not stop the app from running')
    return redirect(url_for('main.home'))


# Delay and pass along any data given
def delay(secs, data):
    sleep(secs)
    return data


# Post ad again using given ad payload in Futures call
def post_ad_again(future):
    if future.done():
        error = future.exception()
        if error:
            print(f'Futures call error: {error}')
        else:
            result = future.result()
            xml_payload = result['payload']
            ad_id_orig = result['ad_id']

            # Post ad again
            ad_id_new = kijiji_api.post_ad(current_user.id, current_user.token, xml_payload)
            print(f'Reposted ad, new ID {ad_id_new}')

            user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)

            # Save ad file
            ad_file_new = os.path.join(user_dir, f'{ad_id_new}.xml')
            with open(ad_file_new, 'w', encoding='utf-8') as f:
                f.write(xml_payload)

            # Delete old ad file
            ad_file_orig = os.path.join(user_dir, f'{ad_id_orig}.xml')
            if os.path.isfile(ad_file_orig):
                os.remove(ad_file_orig)
                print(f'Deleted old ad file for ad {ad_id_orig}')
    elif future.cancelled():
        print('Futures call canceled')


# Overwrite image URLs in ad payload using image URLs from current ad
def translate_image_urls(ad_id, xml_payload):
    data = kijiji_api.get_ad(current_user.id, current_user.token, ad_id)
    payload = xmltodict.parse(xml_payload)
    payload['ad:ad']['pic:pictures'] = data['ad:ad']['pic:pictures']
    return xmltodict.unparse(payload, short_empty_elements=True)


@ad.route('/repost_all')
@login_required
def repost_all():
    # Get all existing ads
    data = kijiji_api.get_ad(current_user.id, current_user.token)

    for ad_id in [ad['@id'] for ad in data['ad:ads']['ad:ad']]:
        repost(ad_id)

    return redirect(url_for('main.home'))
