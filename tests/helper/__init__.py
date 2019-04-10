from gtagora.http.client import Client


class FakeResponse:

    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.data = data
        self.text = ''

    def json(self):
        return self.data


class FakeClient(Client):
    def __init__(self, connection, response=FakeResponse()):
        super().__init__(connection=connection)
        self.response = response

    def check_connection(self):
        return True

    def set_next_response(self, response):
        self.response = response

    def get(self, url, timeout=None, params=None, **kwargs):
        return self.response
