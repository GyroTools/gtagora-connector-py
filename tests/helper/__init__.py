import json as _json
from pathlib import Path

from gtagora.http.client import Client

FIXTURE_DIR = Path(__file__).parent.parent / 'data'


def load_fixture(path: str):
    return _json.loads((FIXTURE_DIR / path).read_text())


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

    def __init__(self, connection):
        super().__init__(connection=connection)
        self._responses = {}
        self.requests = []

    def check_connection(self):
        return True

    def set_response(self, url, response, method=None):
        """Register a response for a specific URL (and optionally HTTP method)."""
        key = f'{method.upper()}:{url}' if method else url
        self._responses[key] = response

    def set_next_response(self, response):
        """Set a fallback response returned for any URL without a specific mapping."""
        self._responses['*'] = response

    def _get_response(self, url, method=None):
        method_url_key = f'{method.upper()}:{url}' if method else None
        return (
            (self._responses.get(method_url_key) if method_url_key else None)
            or self._responses.get(url)
            or self._responses.get('*')
        )

    def _log(self, method, url, data=None):
        self.requests.append({'method': method, 'url': url, 'data': data})

    def get(self, url, timeout=None, params=None, **kwargs):
        self._log('GET', url)
        return self._get_response(url, 'GET')

    def post(self, url, data=None, json=None, timeout=None, params=None, **kwargs):
        self._log('POST', url, json if json is not None else data)
        return self._get_response(url, 'POST')

    def put(self, url, data=None, json=None, timeout=None, params=None, **kwargs):
        self._log('PUT', url, json if json is not None else data)
        return self._get_response(url, 'PUT')

    def patch(self, url, data=None, json=None, timeout=None, params=None, **kwargs):
        self._log('PATCH', url, json if json is not None else data)
        return self._get_response(url, 'PATCH')

    def delete(self, url, timeout=None, **kwargs):
        self._log('DELETE', url)
        return self._get_response(url, 'DELETE')
