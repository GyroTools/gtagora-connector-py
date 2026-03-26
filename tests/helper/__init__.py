import json as _json

from gtagora.http.client import Client


class FakeResponse:

    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.data = data
        self.text = ''

    @property
    def content(self):
        return _json.dumps(self.data).encode()

    def json(self):
        return self.data


class FakeClient(Client):
    def __init__(self, connection, response=FakeResponse()):
        super().__init__(connection=connection)
        self.response = response
        self.last_post_url = None
        self.last_post_data = None

    def check_connection(self):
        return True

    def set_next_response(self, response):
        self.response = response

    def get(self, url, timeout=None, params=None, **kwargs):
        return self.response

    def post(self, url, data=None, json=None, timeout=None, params=None, **kwargs):
        self.last_post_url = url
        self.last_post_data = json if json is not None else data
        return self.response
