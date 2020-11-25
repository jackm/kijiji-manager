import uuid
from xml.parsers.expat import ExpatError, errors

import httpx
import xmltodict


class KijijiApiException(Exception):
    pass


class KijijiApi:
    """API for interfacing with Kijiji site

    This class is stateless and does not manage user logins on its own
    Must login first to use methods that require a user ID and token

    Methods raise KijijiApiException on errors
    """
    def __init__(self, session=None):
        if session:
            self.session = session
        else:
            # Kijiji sometimes takes a bit longer to respond to API requests
            # e.g. for loading conversations
            timeout = httpx.Timeout(30.0, connect=30.0)
            self.session = httpx.Client(timeout=timeout)

        # Base API URL
        self.base_url = 'https://mingle.kijiji.ca/api'

        # Common HTTP header fields
        self.headers = {
            'Accept': 'application/xml',
            'Accept-Language': 'en-CA',
            'User-Agent': 'Kijiji 12.9.0 (iPhone; iOS 13.4.1; en_CA)',
            'X-ECG-VER': '1.67',
        }

    def login(self, username, password):
        """Login to Kijiji

        :param username: login username
        :param password: login password
        :return: Tuple of user ID and session token
        """
        headers = self.headers
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        payload = {
            'username': username,
            'password': password,
            'socialAutoRegistration': 'false',
        }

        r = self.session.post(self.base_url + '/users/login', headers=headers, data=payload)

        doc = self._parse_response(r.text)

        if r.status_code == 200:
            try:
                user_id = doc['user:user-logins']['user:user-login']['user:id']
                email = doc['user:user-logins']['user:user-login']['user:email']
                token = doc['user:user-logins']['user:user-login']['user:token']
            except KeyError as e:
                raise KijijiApiException("User ID and/or user token not found in response text: {}".format(e))
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
        url = '/users/{}/ads'.format(user_id)
        if ad_id:
            url += '/{}'.format(ad_id)
        else:
            # Query all ads
            url += '?size=50' \
                   '&page=0' \
                   '&_in=id,title,price,ad-type,locations,ad-status,category,pictures,start-date-time,features-active,view-ad-count,user-id,phone,email,rank,ad-address,phone-click-count,map-view-count,ad-source-id,ad-channel-id,contact-methods,attributes,link,description,feature-group-active,end-date-time,extended-info,highest-price'

        r = self.session.get(self.base_url + url, headers=headers)

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

        r = self.session.get(self.base_url + '/users/{}/profile'.format(user_id), headers=headers)

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

        r = self.session.delete(self.base_url + '/users/{}/ads/{}'.format(user_id, ad_id), headers=headers)

        if r.status_code == 204:
            return True
        else:
            raise KijijiApiException(self._error_reason(self._parse_response(r.text)))

    def post_ad(self, user_id, token, data):
        """Post new ad

        :param user_id: user ID number
        :param token: session token
        :param data: ad xml data
        :return: new ad ID number
        """
        headers = self._headers_with_auth(user_id, token)
        headers.update({'Content-Type': 'application/xml'})

        # Expects data to be in correct XML format
        xml = data

        r = self.session.post(self.base_url + '/users/{}/ads'.format(user_id), headers=headers, data=xml)

        doc = self._parse_response(r.text)

        if r.status_code == 201:
            try:
                ad_id = doc['ad:ad']['@id']
            except KeyError as e:
                raise KijijiApiException("User ID and/or user token not found in response text: {}".format(e))
            return ad_id
        else:
            raise KijijiApiException(self._error_reason(doc))

    def upload_image(self, data):
        """Upload image using eBay API

        :param data: werkzeug.FileStorage type image object
        :return: full image URL
        """

        # Generate random multipart form boundary value
        boundary = uuid.uuid4()

        # Image upload host uses a separate set of headers
        headers = {
            'Content-Type': 'multipart/form-data; boundary={boundary}'.format(boundary=boundary),
            'User-Agent': 'okhttp/4.9.0',
            'X-EBAY-API-CALL-NAME': 'UploadSiteHostedPictures',
        }

        # TODO: Use xmltodict.unparse to create XML payload
        # TODO: Force set "name" subfield to "Kijiji CA Image" in Content-Disposition header of image data?
        #  Content-Disposition: form-data; name="Kijiji CA Image"; filename="image.jpg"
        #  Content-Type: image/jpeg
        payload = """--{boundary}
Content-Disposition: form-data; name="XML Payload"
Content-Transfer-Encoding: binary
Content-Type: multipart/form-data; charset=utf-8
Content-Length: 1267

<?xml version="1.0" encoding="utf-8"?>
<UploadSiteHostedPicturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
<RequesterCredentials>
<ebl:eBayAuthToken xmlns:ebl="urn:ebay:apis:eBLBaseComponents">AgAAAA**AQAAAA**aAAAAA**794AVA**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6AFloGkCpeKpwidj6x9nY+seQ**j8wBAA**AAMAAA**Dcq42e67om1UK0nk3SitvstDX+8xtEjuOgRWkML+CoPeyWHuYrwlJN5vO00GuY3f4WSQTxu+S/9FVYHjdrjOMGOrMdcuNTwOO+rGtiY/Tkt0r5bQu74ss4Ljep0XG50U+nN57H0LMloGUb7qM78tyfG7lZp08LSfa1bwrOXXqBpLGcA2tg+y+6IrVl6MMRVQurWHQR1UVnE2hhmJghsGb2KYF9jrw+Sh1DYjaYvV4vbPN/G6CtBjCyq8Y02Mli9LmBwZAmzJ5lBEysYGDAd0cYZJQJdel/jpOSC6yDH6hJ2VTmqkAhFObNWf5zJi1I1NHJU857r9Mfj16xiC4BQXTLk/e3Ka4bfwkQKtAZWYBp5H17xC/IOU3Z+4UBQaGo3br7ST0rD5BbDRDFobWLAaLy9vG6+KrWQWMciwRJ1yJb9Kl2TH0cJnLq34LBcS2nT8wQKl3Mv0PyKXdj/LTOgxmIGEKQVOVQQr/zejJ8Zk4jEsKwRatwrEN1fc83ZAhdIzftmhk+HPfa5C5m97EoPucu+v+ftVXgfdvA6zqOREJUtxQakAWXsTHJ8xVFPvnt/OtFv9AAtKQ8dBzGQfyadU5ppQqLR5r7C5us9OalJxwvdw87R6Xadhq+eJZIa5xnBIjcOmP4z6wsnHbPldB4MHh5wdnm5qj+PReJMXLpx5XznjmjhmAV6CTbmA4+iNCBwu9qchqOg8tyN0OFmeTUelptAmCl0eXa6KMVHWLvwORQYsbOg55T5f+8UrzqNhc9Ce</ebl:eBayAuthToken>
</RequesterCredentials>
<PictureName>Kijiji CA Image</PictureName>
<PictureSet>Supersize</PictureSet>
<ExtensionInDays>365</ExtensionInDays>
</UploadSiteHostedPicturesRequest>
--{boundary}
""".format(boundary=boundary).encode('utf-8')
        payload += bytes(data.headers.__str__(), 'utf-8')
        payload += data.read()
        payload += '\n--{boundary}--\n'.format(boundary=boundary).encode('utf-8')

        r = self.session.post('https://api.ebay.com/ws/api.dll', headers=headers, data=payload)

        doc = self._parse_response(r.text)

        try:
            if r.status_code == 200 and doc['UploadSiteHostedPicturesResponse']['Ack'] == 'Success':
                return doc['UploadSiteHostedPicturesResponse']['SiteHostedPictureDetails']['FullURL']
            else:
                raise KijijiApiException(self._error_reason_ebay(doc))
        except KeyError:
            raise KijijiApiException(self._error_reason_ebay(doc))

    def get_conversation(self, user_id, token, conversation_id=None):
        """Get all conversations or single conversation by conversation ID number if given

        :param user_id: user ID number
        :param token: session token
        :param conversation_id: conversation ID number
        :return: response data dict
        """
        headers = self._headers_with_auth(user_id, token)
        url = '/users/{}/conversations'.format(user_id)
        if conversation_id:
            url += '/{}?tail=100'.format(conversation_id)
        else:
            # Query all ads
            url += '?size=25'

        r = self.session.get(self.base_url + url, headers=headers)

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
        url = '/users/{}/conversations'.format(user_id)

        # Query all ads
        url += '?size=25&page={}'.format(page)

        r = self.session.get(self.base_url + url, headers=headers)

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
            raise KijijiApiException('direction parameter must be set to either "owner" or "buyer", not "{}"'.format(direction))

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

        r = self.session.post(self.base_url + '/replies/reply-to-ad-conversation', headers=headers, data=xml)

        doc = self._parse_response(r.text)

        if r.status_code == 201:
            return doc
        else:
            raise KijijiApiException(self._error_reason(doc))

    def _headers_with_auth(self, user_id, token):
        headers = self.headers
        headers.update({
            'X-ECG-Authorization-User': 'id="{}", token="{}"'.format(user_id, token),
        })
        return headers

    @staticmethod
    def _parse_response(text):
        try:
            doc = xmltodict.parse(text)
        except ExpatError as e:
            raise KijijiApiException("Unable to parse text: {}".format(errors.messages[e.code]))
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
    def _error_reason_ebay(doc):
        try:
            error = doc['UploadSiteHostedPicturesResponse']['Errors']
            message = "{}: {} {}".format(error['SeverityCode'], error['ShortMessage'], error['LongMessage'])
        except (TypeError, KeyError):
            return 'Unknown eBay API error'
        return message
