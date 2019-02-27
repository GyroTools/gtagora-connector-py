from requests.auth import HTTPBasicAuth

from gtagora.http.auth import ApiKeyAuth


class Connection:
    def __init__(self, url):
        self.url = url
        self.verify_certificate = True

    def get_auth(self):
        raise NotImplementedError


class BasicConnection(Connection):
    def __init__(self, url, user=None, password=None):
        super().__init__(url)
        self.user = user
        self.password = password

    def get_auth(self):
        return HTTPBasicAuth(self.user, self.password)


class ApiKeyConnection(Connection):
    def __init__(self, url, api_key=None):
        super().__init__(url)
        self.api_key = api_key

    def get_auth(self):
        return ApiKeyAuth(self.api_key)
