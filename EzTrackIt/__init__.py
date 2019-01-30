from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
from collections import OrderedDict
import requests
import json

__base__ = 'https://uriuexpress.eztrackit-discovery.com/api'


urls = {
    'api_base': __base__,
    'token': __base__ + '/users/auth',
    'recipients': __base__ + '/recipients',
    'packages': __base__ + '/packages'
}

delivery_modes = {
    'delivery': 1,
    'forward': 2,
    'return': 3
}

notification_ids = {
    'staff': 1,
    'student': 2
}

notification_types = {
    'email': 1,
    'sms': 2,
    'all': 3
}


class Recipient:
    def __init__(self, first_name, last_name, internal_id, email, company=None,
            joint_account_holder=None, mailbox=None, phone_number=None, mobile_number=None, 
            primary=1, notification_type=1, notification_id=2, address=None, apartment=None, city=None, 
            state=None, zip_code=None, country=None, delivery_mode=1,
            send_notification=True, notes=None, id=None):

        self.id = id
        self.first_name = first_name # FirstName
        self.last_name = last_name # LastName
        self.internal_id = internal_id # internalID
        self.joint_account_holder = joint_account_holder # jointAccountHolder
        self.email = email
        self.mailbox = mailbox
        self.phone_number = phone_number # phoneNumber
        self.mobile_number = mobile_number # mobileNumber
        self.primary = primary # primary
        

        self.delivery_mode = delivery_mode

        # send notification
        if isinstance(send_notification, bool):
            self.send_notification = int(send_notification)
        else:
            self.send_notification = 1

        self.notification = OrderedDict()
        self.notification['id'] = notification_id
        self.notification['type'] = notification_type


        self.address = {}
        self.address['administrativeArea'] = state
        self.address['country'] = country
        self.address['organisationName'] = company
        self.address['locality'] = city
        self.address['postalCode'] = zip_code
        self.address['thoroughfare'] = address
        self.address['premise'] = apartment

        self.notes = notes

    def __repr__(self):
        return("<Recipient(id={}, first_name={}, last_name={}, internal_id={}>".format(
            self.id, self.first_name, self.last_name, self.internal_id))

    def json(self):
        output = OrderedDict()

        output['firstName'] = self.first_name
        output['lastName'] = self.last_name
        output['deliveryMode'] = self.delivery_mode

        output['address'] = {}
        output['address']['country'] = None
        for key, val in self.address.items():
            if val is not None:
                output['address'][key] = val

        output['email'] = self.email
        output['primary'] = self.primary
        if self.joint_account_holder is not None:
            output['jointAccountHolder'] = self.joint_account_holder

        output['internalId'] = self.internal_id
        if self.mailbox is not None:
            output['mailbox'] = self.mailbox

        output['notification'] = {}
        for key, val in self.notification.items():
            if val is not None:
                output['notification'][key] = val

        if self.mobile_number is not None and self.mobile_number != 'false':
            output['mobileNumber'] = self.mobile_number

        if self.phone_number is not None and self.phone_number != 'false':
            output['phoneNumber'] = self.phone_number

        output['sendNotification'] = self.send_notification

        # if len(output['notification']) == 0:
        #    output.pop('notification')
        return json.dumps(output)


class ApiResponse:
    def __init__(self, json, page=1, pages=1, total=1, limit=1, links=None):
        self.json = json

        self.page = page
        self.pages = pages
        self.total = total
        self.limit = limit
        self.links = links

        if '_embedded' in json:
            self.data = json['_embedded']
            # collapse result if only one key
            if len(self.data.keys()) == 1:
                key, self.data = self.data.popitem()
        else: 
            self.data = json

        if 'limit' in json: self.limit = json['limit'] 
        if 'page' in json: self.page = json['page']
        if 'pages' in json: self.pages = json['pages']
        if '_links' in json: self.links = json['_links'] 
        if 'total' in json: self.total = json['total']

    def __repr__(self):
        return '<ApiResponse(limit={},page={},pages={},total={})>'.format(
            self.limit, self.page, self.pages, self.total)


class EzTrackIt:
    def __init__(self, client_id, token_url=urls['token'], token=None):
        self.client_id = client_id
        self.token_url = token_url
        self._token = token
        self._oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.client_id), token=token)
    
    def login(self, username, password):
        if self._token is None:
            self._token = self._oauth.fetch_token(
                token_url=self.token_url,
                username=username,
                password=password,
                client_id=self.client_id,
                auth=False)
        requests.utils.add_dict_to_cookiejar(self._oauth.cookies, {
            "access_token": self._token.get("access_token"),
            "refresh_token": self._token.get("refresh_token")})
        return self._oauth.authorized
    
    def api_get(self, resource_url):
        response = json=self._oauth.get(resource_url)
        response.raise_for_status()
        return ApiResponse(json=response.json())
    
    def api_patch(self, resource_url, json):
        response = self._oauth.patch(url=resource_url, data=json)
        return response

    def api_post(self, resource_url, json):
        return self._oauth.patch(url=resource_url, data=json)

    def session(self):
        return self._oauth

    def token(self):
        return self._token


def get_recipients(client):
    response = client.api_get(urls['recipients'] + "?sort=id&sortOrder=asc&limit=100")
    yield response.data
    pages = range(response.page + 1, response.pages + 1)
    for i in pages:
        response = client.api_get(urls['recipients'] + "?sort=id&sortOrder=asc&limit=100&page={}".format(i))
        yield response.data


def get_recipient(client, search):
    response = client.api_get(urls['recipients'] + "?sort=id&sortOrder=asc&limit=5&search={0}".format(search))
    return response.data


def get_packages(client, recipient_id):
    response = client.api_get(urls['packages'] + "?recipient={}&searchField=checkedIn".format(recipient_id))
    return response.data


def get_packages_for_recipient(client, student_number, notified_only=True):
    for r in get_recipient(client=client, search=student_number):
        if r['internal_id'] == student_number:
            packages = get_packages(client=client, recipient_id=r['id'])

            if notified_only:
                packages = [pkg for pkg in packages if pkg.get('notified', None) is not None]

            return packages
