from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
from xml.parsers.expat import ExpatError, errors

import httpx
import pgeocode
import xmltodict


class KijijiApiException(Exception):
    """KijijiApi class exception"""


class KijijiApi:
    """API for interfacing with Kijiji site

    This class is stateless and does not manage user logins on its own.
    Must login first to use methods that require a user ID and token.

    Methods raise KijijiApiException on errors
    """
    def __init__(self, session=None):

        # Base API URL
        self.base_url = 'https://mingle.kijiji.ca/api'

        # Kijiji app version number
        self.app_ver = '17.7.0'

        # Common HTTP header fields
        self.headers = {
            'Accept': 'application/xml',
            'Accept-Language': 'en-CA',
            'User-Agent': f'com.ebay.kijiji.ca {self.app_ver} (LGE Nexus 5; Android 6.0.1; en_US)',
            'X-ECG-VER': '3.6',
        }

        if session:
            if not isinstance(session, httpx.Client):
                raise KijijiApiException("'session' kwarg must be an httpx.Client object")

            self.session = session

            # Append common headers
            self.session.headers = self.headers
        else:
            # Kijiji sometimes takes a bit longer to respond to API requests
            # e.g. for loading conversations
            timeout = httpx.Timeout(30.0, connect=30.0)
            self.session = httpx.Client(timeout=timeout, headers=self.headers)

    def login(self, username, password):
        """Login to Kijiji

        :param username: login username
        :param password: login password
        :return: Tuple of user ID and session token
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'username': username,
            'password': password,
            'socialAutoRegistration': 'false',
        }

        r = self.session.post(f'{self.base_url}/users/login', headers=headers, data=payload)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            try:
                user_id = doc['user:user-logins']['user:user-login']['user:id']
                email = doc['user:user-logins']['user:user-login']['user:email']
                token = doc['user:user-logins']['user:user-login']['user:token']
            except KeyError as e:
                raise KijijiApiException(f"User ID and/or user token not found in response text: {e}")
            return user_id, token
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_ad(self, user_id, token, ad_id=None):
        """Get existing ad(s)

        If ad_id is left unspecified, query all ads

        :param user_id: user ID number
        :param token: session token
        :param ad_id: ad ID number
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)
        url = f'{self.base_url}/users/{user_id}/ads'
        if ad_id:
            url += f'/{ad_id}'
        else:
            # Query all ads
            url += '?size=50' \
                   '&page=0' \
                   '&_in=id,title,price,ad-type,locations,ad-status,category,pictures,start-date-time,features-active,view-ad-count,user-id,phone,email,rank,ad-address,phone-click-count,map-view-count,ad-source-id,ad-channel-id,contact-methods,attributes,link,description,feature-group-active,end-date-time,extended-info,highest-price'

        r = self.session.get(url, headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_profile(self, user_id, token):
        """Get profile data

        :param user_id: user ID number
        :param token: session token
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)

        r = self.session.get(f'{self.base_url}/users/{user_id}/profile', headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_categories(self, user_id, token):
        """Get all categories metadata

        :param user_id: user ID number
        :param token: session token
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)

        r = self.session.get(f'{self.base_url}/categories', headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_locations(self, user_id, token):
        """Get all locations metadata

        :param user_id: user ID number
        :param token: session token
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)

        r = self.session.get(f'{self.base_url}/locations', headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_attributes(self, user_id, token, attr_id):
        """Get ad attributes metadata

        :param user_id: user ID number
        :param token: session token
        :param attr_id: attribute ID number
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)

        r = self.session.get(f'{self.base_url}/ads/metadata/{attr_id}', headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def delete_ad(self, user_id, token, ad_id):
        """Delete ad

        :param user_id: user ID number
        :param token: session token
        :param ad_id: ad ID number
        :return: boolean indicating if deletion was successful
        """
        headers = self._headers_with_auth(user_id, token)

        r = self.session.delete(f'{self.base_url}/users/{user_id}/ads/{ad_id}', headers=headers)

        if r.status_code == 204:
            return True
        else:
            raise KijijiApiException(self._error_reason(self._parse_response(r.text)))

    def post_ad(self, user_id, token, data):
        """Post new ad

        No input validation is performed; incorrect inputs are expected to be reported back by Kijiji API after attempting to post

        :param user_id: user ID number
        :param token: session token
        :param data: ad xml data
        :return: new ad ID number
        """
        headers = self._headers_with_auth(user_id, token)
        headers.update({'Content-Type': 'application/xml'})

        # Expects data to be in correct XML format
        xml = data

        r = self.session.post(f'{self.base_url}/users/{user_id}/ads', headers=headers, data=xml)

        doc = self._parse_response(r.text)

        if r.status_code == 201:
            try:
                ad_id = doc['ad:ad']['@id']
            except KeyError as e:
                raise KijijiApiException(f"User ID and/or user token not found in response text: {e}")
            return ad_id
        else:
            raise KijijiApiException(self._error_reason(doc))

    def upload_image(self, user_id, token, data):
        """Upload image Kijiji mobile API

        :param user_id: user ID number
        :param token: session token
        :param data: werkzeug.FileStorage type image object
        :return: full image URL
        """

        api_endpoint = 'https://mobile-api.kijiji.ca/v1/images/upload'

        headers = self._headers_with_auth(user_id, token)
        headers.update({
            'Accept': 'application/json',
            'X-ECG-Platform': 'android',
            'X-ECG-App-Version': self.app_ver,
        })

        # Image expiration epoch timestamp
        # Kijiji sets this to 199 days, 23 hours from now
        expiration_timestamp = int((datetime.today() + timedelta(days=199, hours=23)).timestamp())

        # Multipart form data
        files = {
            'bucketAlias': (None, b'ca-prod-fsbo-ads'),
            'objectExpiration': (None, str(expiration_timestamp).encode('utf-8')),
            'file': (data.filename, data.read(), data.content_type),
        }

        r = self.session.post(api_endpoint, headers=headers, files=files)

        # Response is in JSON format
        doc = r.json()

        if r.status_code == 201:
            try:
                url = doc['url']
            except KeyError as e:
                raise KijijiApiException(f"Image URL not found in response text: {e}")

            # Query string is appended to URL to specify image size (thumbnail size by default)
            # Strip all query strings from URL
            url = urlunparse(urlparse(url)._replace(query=''))

            return url
        else:
            raise KijijiApiException(self._error_reason_mobile(doc))

    def get_conversation(self, user_id, token, conversation_id=None):
        """Get all conversations or single conversation by conversation ID number if given

        :param user_id: user ID number
        :param token: session token
        :param conversation_id: conversation ID number
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)
        url = f'{self.base_url}/users/{user_id}/conversations'
        if conversation_id:
            url += f'/{conversation_id}?tail=100'
        else:
            # Query all ads
            url += '?size=25'

        r = self.session.get(url, headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def get_conversation_page(self, user_id, token, page):
        """Get conversation by page number.

        :param user_id: user ID number
        :param token: session token
        :param page: conversation page number
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)
        url = f'{self.base_url}/users/{user_id}/conversations'

        # Query all ads
        url += f'?size=25&page={page}'

        r = self.session.get(url, headers=headers)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def post_conversation_reply(self, user_id, token, conversation_id, ad_id, username, email, message, direction, phone=None):
        """Post conversation reply

        :param user_id: user ID number
        :param token: session token
        :param conversation_id: conversation ID number
        :param ad_id: ad ID number
        :param username: reply username
        :param email: reply email
        :param message: reply message
        :param direction: reply direction; can be either 'owner' if sending to ad owner or 'buyer' if sending to potential ad buyer
        :param phone: phone number string
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)
        headers.update({'Content-Type': 'application/xml'})

        # Determine direction
        # Set to appropriate string value
        if direction.lower() == 'owner':
            direction = 'TO_OWNER'
        elif direction.lower() == 'buyer':
            direction = 'TO_BUYER'
        else:
            raise KijijiApiException(f'direction parameter must be set to either "owner" or "buyer", not "{direction}"')

        payload = {
            'reply:reply-to-ad-conversation': {
                '@xmlns:reply': 'http://www.ebayclassifiedsgroup.com/schema/reply/v1',
                '@xmlns:types': 'http://www.ebayclassifiedsgroup.com/schema/types/v1',
                'reply:ad-id': ad_id,
                'reply:conversation-id': conversation_id,
                'reply:reply-username': username,
                'reply:reply-email': email,
                'reply:reply-phone': phone,
                'reply:reply-message': message,
                'reply:reply-direction': {'types:value': direction},
            }
        }

        # Payload is an XML string
        xml = xmltodict.unparse(payload, short_empty_elements=True, pretty=True)

        r = self.session.post(f'{self.base_url}/replies/reply-to-ad-conversation', headers=headers, data=xml)

        doc = self._parse_response(r.text)

        if r.status_code == 201:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))
    
    def geo_location(self, postal_code):
        # pgeocode.Nominatim.query_postal_code only uses the first three characters to do the lookup for Canadian postal codes
        postalcode = postal_code[:3]
        try:
            nomi = pgeocode.Nominatim('ca')
            location = nomi.query_postal_code(postalcode)
        except Exception as e:
            raise KijijiApiException(f'Error acquiring geo location data: {e}')
        else:
            return location
    
    @staticmethod
    def _headers_with_auth(user_id, token):
        return {'X-ECG-Authorization-User': f'id="{user_id}", token="{token}"'}

    @staticmethod
    def _parse_response(text):
        try:
            doc = xmltodict.parse(text)
        except ExpatError as e:
            raise KijijiApiException(f"Unable to parse text: {errors.messages[e.code]}")
        return doc

    @staticmethod
    def _error_reason(doc):
        try:
            base = doc['api-base-error']
            if 'api-field-errors' in base and base['api-field-errors']:
                base = base['api-field-errors']['api-field-error']
            error = base['api-errors']['api-error']
            message = error['message']
        except (TypeError, KeyError):
            return 'Unknown API error'
        return message

    @staticmethod
    def _error_reason_mobile(doc):
        try:
            return doc['message']
        except KeyError:
            return 'Unknown mobile API error'
