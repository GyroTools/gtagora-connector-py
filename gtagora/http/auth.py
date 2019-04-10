import requests


class ApiKeyAuth(requests.auth.AuthBase):

    def __init__(self, api_key=None):
        self.api_key = api_key

    def __call__(self, r):
        r.headers['Authorization'] = 'X-Agora-Api-Key ' + self.api_key
        return r


class TokenAuth(requests.auth.AuthBase):

    def __init__(self, token=None):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Token ' + self.token
        return r


class NoAuth(requests.auth.AuthBase):

    def __call__(self, r):
        return r