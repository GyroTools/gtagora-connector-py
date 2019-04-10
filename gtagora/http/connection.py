from requests.auth import HTTPBasicAuth

from gtagora.http.auth import ApiKeyAuth, TokenAuth, NoAuth


class Connection:
    def __init__(self, url, verify_certificate=True):
        self.url = url
        self.verify_certificate = verify_certificate

    def get_auth(self):
        raise NotImplementedError


class BasicConnection(Connection):
    def __init__(self, url, user, password, verify_certificate=True):
        super().__init__(url, verify_certificate=verify_certificate)
        self.user = user
        self.password = password

    def get_auth(self):
        return HTTPBasicAuth(self.user, self.password)


class ApiKeyConnection(Connection):
    def __init__(self, url, api_key, verify_certificate=True):
        super().__init__(url, verify_certificate=verify_certificate)
        self.api_key = api_key

    def get_auth(self):
        return ApiKeyAuth(self.api_key)


class TokenConnection(Connection):
    def __init__(self, url, verify_certificate=True):
        super().__init__(url, verify_certificate=verify_certificate)
        self.token = None

    def get_auth(self):
        if self.token:
            return TokenAuth(self.token)
        return NoAuth()

    def login(self, client, user, password):
        response = client.post("/api/v1/rest-auth/login/", data={'username': user, 'password': password})
        if response.status_code == 200:
            self.token = response.json()['key']
        else:
            raise Exception(response.text)