import json
import os
from time import sleep

import xmltodict
from flask import Blueprint, flash, render_template, redirect, url_for, session, current_app, request
from flask_executor import Executor
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, DateField

from kijiji_manager.common import get_category_data, get_location_data, get_attrib
from kijiji_manager.forms.post import CategoryForm, PostForm
from kijiji_manager.kijijiapi import KijijiApi

executor = Executor()

ad = Blueprint('ad', __name__)


@ad.route('/ad/<ad_id>')
@login_required
def show(ad_id):
    data = KijijiApi().get_ad(current_user.id, current_user.token, ad_id)
    return render_template('ad.html', data=data)


@ad.route('/delete/<ad_id>')
@login_required
def delete(ad_id):
    KijijiApi().delete_ad(current_user.id, current_user.token, ad_id)
    flash('Deleted ad %s' % ad_id)
    return redirect(url_for('main.home'))


@ad.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    # Multi-step form
    step1 = 'choose_category'
    step2 = 'fill_attributes'
    step3 = 'submit'

    category_form = CategoryForm()
    category_form.cat1.choices = [(cat['@id'], cat['cat:id-name']) for cat in get_category_data()['cat:categories']['cat:category']['cat:category']]

    form = PostForm()

    if 'step' not in request.form:
        # Step 1: Choose ad category

        return render_template('post.html', form=category_form, step=step1, next_step=step2)

    elif request.form['step'] == step2:
        # Step 2: Fill in ad attributes

        if not category_form.validate_on_submit():
            flash(category_form.errors)
            return redirect(url_for('.post'))

        # Get most significant category ID from given set of categories in previous step form
        category_choice = (lambda x1, x2, x3: x3 if x3 else x2 if x2 else x1)(category_form.cat1.data, category_form.cat2.data, category_form.cat3.data)
        session['category'] = category_choice
        data = get_attrib(category_choice)

        # Update supported ad type choices
        try:
            form.adtype.choices = [(x['#text'], x['@localized-label']) for x in data['ad:ad']['ad:ad-type']['ad:supported-value']]
            session['adtype.choices'] = form.adtype.choices
        except KeyError:
            flash('No supported ad types available')

        # Location options
        locations = get_location_data()
        try:
            location_list = [(loc['@id'], loc['loc:localized-name']) for loc in locations['loc:locations']['loc:location']['loc:location']]
        except KeyError:
            # Only one location
            location_list = locations['loc:locations']['loc:location']['loc:localized-name']
        form.loc1.choices = location_list
        session['loc1.choices'] = form.loc1.choices

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
                        item = {'label': {attrib['@name']: attrib['@localized-label']}}

                        if attrib['@type'] == 'ENUM':
                            item.update({'choices': {}})
                            if 'attr:supported-value' in attrib:
                                for value in attrib['attr:supported-value']:
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

        return render_template('post.html', form=form, step=step2, next_step=step3, attrib_form=attrib_form, attrib=category_choice)

    elif request.form['step'] == step3:
        if not form.validate_on_submit():
            flash(form.errors)

            # Restore dynamic form data
            if not form.adtype.choices:
                form.adtype.choices = session.get('adtype.choices', [])
            if not form.loc1.choices:
                form.loc1.choices = session.get('loc1.choices', [])
            attrib_form = create_attribute_form(session.get('attrib_types'))

            return render_template('post.html', form=form, step=step2, next_step=step3, attrib_form=attrib_form, attrib=session.get('category'))

        # Get most significant location ID from given set of locations in previous step form
        # Default to 'Canada' => '0' if none given
        location_choice = (lambda x1, x2, x3: x3 if x3 else x2 if x2 else x1 if x1 else '0')(form.loc1.data, form.loc2.data, form.loc3.data)

        # Get submitted form items
        # Split form items into persistent form item and remaining items
        postform_fields = list(vars(PostForm())['_fields'].keys())
        attrs_postform = {}
        attrs_attrform = {}
        for key, value in request.form.items():
            # Filter out persistent form items (fields in PostForm class) to determine dynamic attributes
            if key in postform_fields:
                # Gather PostForm items
                attrs_postform[key] = value
            else:
                # Gather AttributeForm items
                attrs_attrform[key] = value

        # Build attributes payload
        attributes_payload = {}
        if attrs_attrform:
            attributes_payload = {'attr:attributes': {'attr:attribute': []}}
            for key, value in attrs_attrform.items():
                # Boolean attribute values must be a string of 'true' or 'false'
                if value is True or value == 'y':
                    value = 'true'
                elif value is False or value == 'n':
                    value = 'false'

                attributes_payload['attr:attributes']['attr:attribute'].append({
                    '@type': '',
                    '@localized-label': '',
                    '@name': key,
                    'attr:value': value,
                })

        # Begin assembling entire payload
        response_payload = {
            'ad:ad': {
                '@xmlns:types': 'http://www.ebayclassifiedsgroup.com/schema/types/v1',
                '@xmlns:cat': 'http://www.ebayclassifiedsgroup.com/schema/category/v1',
                '@xmlns:loc': 'http://www.ebayclassifiedsgroup.com/schema/location/v1',
                '@xmlns:ad': 'http://www.ebayclassifiedsgroup.com/schema/ad/v1',
                '@xmlns:attr': 'http://www.ebayclassifiedsgroup.com/schema/attribute/v1',
                '@xmlns:pic': 'http://www.ebayclassifiedsgroup.com/schema/picture/v1',
                '@xmlns:user': 'http://www.ebayclassifiedsgroup.com/schema/user/v1',
                '@xmlns:rate': 'http://www.ebayclassifiedsgroup.com/schema/rate/v1',
                '@xmlns:reply': 'http://www.ebayclassifiedsgroup.com/schema/reply/v1',
                '@locale': 'en-CA',
            }
        }
        for key, value in attrs_postform.items():
            if key == 'adtype':
                response_payload['ad:ad'].update({'ad:ad-type': {'ad:value': value}})
            elif key == 'adtitle':
                response_payload['ad:ad'].update({'ad:title': value})
            elif key == 'description':
                response_payload['ad:ad'].update({'ad:description': value})
            elif key == 'postalcode':
                if 'ad:ad-address' not in response_payload['ad:ad']:
                    response_payload['ad:ad'].update({'ad:ad-address': {}})
                response_payload['ad:ad']['ad:ad-address'].update({'types:zip-code': value})
            elif key == 'fulladdress':  # Yet to be implemented
                if 'ad:ad-address' not in response_payload['ad:ad']:
                    response_payload['ad:ad'].update({'ad:ad-address': {}})
                response_payload['ad:ad']['ad:ad-address'].update({'types:full-address': value})
            elif key == 'pricetype':
                if 'ad:price' not in response_payload['ad:ad']:
                    response_payload['ad:ad'].update({'ad:price': {}})
                response_payload['ad:ad']['ad:price'].update({'types:price-type': {'types:value': value}})
            elif key == 'price':
                if 'ad:price' not in response_payload['ad:ad']:
                    response_payload['ad:ad'].update({'ad:price': {}})
                response_payload['ad:ad']['ad:price'].update({'types:amount': value})
        if location_choice:
            response_payload['ad:ad'].update({'loc:locations': {'loc:location': {'@id': location_choice}}})
        if session['category']:
            response_payload['ad:ad'].update({'cat:category': {'@id': session['category']}})
        if current_user.id:
            response_payload['ad:ad'].update({'ad:account-id': current_user.id})
        if current_user.email:
            response_payload['ad:ad'].update({'ad:email': current_user.email})
        if current_user.name:
            response_payload['ad:ad'].update({'ad:poster-contact-name': current_user.name})
        if attributes_payload:
            response_payload['ad:ad'].update(attributes_payload)

        # Create picture payload
        pictures_payload = create_picture_payload(form)
        if pictures_payload:
            response_payload['ad:ad'].update(pictures_payload)

        xml_payload = xmltodict.unparse(response_payload, short_empty_elements=True, pretty=True)

        # Submit final payload
        ad_id = KijijiApi().post_ad(current_user.id, current_user.token, xml_payload)
        flash('Ad %s posted!' % ad_id)

        # Save ad payload
        user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        ad_file = os.path.join(user_dir, ad_id + '.xml')
        with open(ad_file, 'w') as f:
            f.write(xml_payload)

        return redirect(url_for('main.home'))


# Build dynamic attribute form
# TODO: Find a better method
#  https://stackoverflow.com/q/28375565
#  https://stackoverflow.com/a/57548509/7781935
def create_attribute_form(types):
    # Insert field attribute to form object
    def insert_attr(obj, field_type, data):
        try:
            for field_id, title in data['label'].items():
                if field_type == SelectField:
                    choices = [c for c in data['choices'].items()]
                    setattr(obj, field_id, field_type(title, choices=choices))
                else:
                    setattr(obj, field_id, field_type(title))
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
            insert_attr(AttributeForm, DateField, item)

        for item in types.get('bools', []):
            insert_attr(AttributeForm, BooleanField, item)

        # Create attributes for anything caught by exceptions during attributes xml parsing, assuming enum type
        for item in types['excepts']:
            insert_attr(AttributeForm, SelectField, item)

    return AttributeForm()


# Build picture payload dict from form.file* fields
def create_picture_payload(form):
    payload = {'pic:pictures': {'pic:picture': []}}
    picture_added = False
    for field in vars(PostForm())['_fields'].keys():
        if field.startswith('file'):
            data = getattr(form, field).data
            if data:
                picture_added = True
                link = KijijiApi().upload_image(data)
                payload['pic:pictures']['pic:picture'].append({'pic:link': {'@rel': 'saved', '@href': link}})
    return payload if picture_added else {}


@ad.route('/repost/<ad_id>')
@login_required
def repost(ad_id):
    # Get existing ad
    user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)
    ad_file = os.path.join(user_dir, ad_id + '.xml')

    if not os.path.isfile(ad_file):
        flash('Cannot repost, ad file {} does not exist'.format(ad_file))
        return redirect(url_for('main.home'))

    with open(ad_file, 'r') as f:
        xml_payload = f.read()

    # Delete existing ad
    KijijiApi().delete_ad(current_user.id, current_user.token, ad_id)
    flash('Deleted old ad %s' % ad_id)

    # Delay and then run callback to post ad again
    future_response = executor.submit(delay, {'payload': xml_payload, 'ad_id': ad_id})
    future_response.add_done_callback(post_ad_again)

    flash('Reposting ad in background after 3 minute delay... Do not stop the app from running')
    return redirect(url_for('main.home'))


# Delay and pass along any data given
def delay(data):
    # Waiting for 3 minutes appears to be enough time for Kijiji to not consider it a duplicate ad
    sleep(3 * 60)
    return data


# Post ad again using given ad payload in Futures call
def post_ad_again(future):
    if future.done():
        error = future.exception()
        if error:
            print('Futures call error: {}'.format(error))
        else:
            result = future.result()
            xml_payload = result['payload']
            ad_id_orig = result['ad_id']

            # Post ad again
            ad_id_new = KijijiApi().post_ad(current_user.id, current_user.token, xml_payload)
            print('Reposted ad, new ID {}'.format(ad_id_new))

            user_dir = os.path.join(current_app.instance_path, 'user', current_user.id)

            # Save ad file
            ad_file_new = os.path.join(user_dir, ad_id_new + '.xml')
            with open(ad_file_new, 'w') as f:
                f.write(xml_payload)

            # Delete old ad file
            ad_file_orig = os.path.join(user_dir, ad_id_orig + '.xml')
            if os.path.isfile(ad_file_orig):
                os.remove(ad_file_orig)
                print('Deleted old ad file for ad {}'.format(ad_id_orig))
    elif future.cancelled():
        print('Futures call canceled')
