import re

import phonenumbers
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, StringField, TextAreaField, DecimalField, SubmitField
from wtforms.validators import InputRequired, Optional, Length, NumberRange, Regexp, ValidationError


class RequiredIfFieldEqualTo(InputRequired):
    """Validator which makes a field required if another field is set and has a desired value"""

    def __init__(self, other_field_name, value, *args, **kwargs):
        self.other_field_name = other_field_name
        self.value = value
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise ValidationError('No field named "%s" in form' % self.other_field_name)
        if other_field.data == self.value:
            super().__call__(form, field)


class PostalCode(Regexp):
    """Validate postal code"""

    def __init__(self, message=None):
        if not message:
            message = 'Invalid postal code'
        regex_postal_code = r'^[ABCEGHJKLMNPRSTVXY]{1}\d{1}[A-Z]{1} *\d{1}[A-Z]{1}\d{1}$'
        super().__init__(regex_postal_code, flags=re.IGNORECASE, message=message)


class PhoneNumber:
    """Validate phone number"""

    def __init__(self, message=None):
        if not message:
            message = 'Invalid phone number'
        self.message = message

    def __call__(self, form, field):
        try:
            p = phonenumbers.parse(field.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError(self.message)


class CategoryForm(FlaskForm):
    """Choose category form"""

    # Only validate top level category choice
    # Subcategory choices are dynamic
    cat1 = SelectField('Category', [InputRequired()])
    cat2 = SelectField(validate_choice=False)
    cat3 = SelectField(validate_choice=False)

    submit = SubmitField('Next')


class PostForm(FlaskForm):
    """Ad post form"""

    adtype = SelectField('Ad Type', choices=[], validate_choice=False)
    adtitle = StringField('Ad Title', [InputRequired(), Length(min=8, max=64, message='Title must be between %(min)d and %(max)d characters')])
    description = TextAreaField('Description', [InputRequired(), Length(min=10, message='Description must be %(min)d or more characters')])

    pricetype_choices = [
        ('SPECIFIED_AMOUNT', 'Specified Amount'),  # First element in list must be for a dollar amount
        ('FREE', 'Free'),
        ('PLEASE_CONTACT', 'Please Contact'),
        ('SWAP_TRADE', 'Swap/Trade'),
    ]
    pricetype = SelectField('Price Type', choices=pricetype_choices)
    price = DecimalField('Price', [RequiredIfFieldEqualTo('pricetype', pricetype_choices[0][0]), NumberRange(min=1), Optional()])

    loc1 = SelectField('Location', validate_choice=False)
    loc2 = SelectField(validate_choice=False)
    loc3 = SelectField(validate_choice=False)
    postalcode = StringField('Postal Code', [InputRequired(), PostalCode()])
    # TODO: Implement full address field
    #fulladdress = StringField('Full Address')
    phone = StringField('Phone', [PhoneNumber(), Optional()])

    images = ['jpg', 'jpeg', 'png', 'gif', 'bmp']  # Kijiji supported image formats
    file1 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file2 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file3 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file4 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file5 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file6 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file7 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file8 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file9 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])
    file10 = FileField('Pictures', [FileAllowed(images, 'Must be an image file')])

    submit = SubmitField('Post Ad')


class PostManualForm(FlaskForm):
    """Ad manual post form"""

    file = FileField('Ad payload file', [FileRequired(), FileAllowed(['xml'], 'Must be an XML file')])
    submit = SubmitField('Post Ad')
