import requests


class ApiKeyAuth(requests.auth.AuthBase):

    def __init__(self, api_key=None):
        self.api_key = api_key

    def __call__(self, r):
        r.headers['Authorization'] = 'X-Agora-Api-Key ' + self.api_key
        return r
