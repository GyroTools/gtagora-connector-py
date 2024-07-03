from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.http.client import Client
from gtagora.models.base import get_client


class User(BaseModel):
    BASE_URL = '/api/v1/user/'

    @classmethod
    def get_current_user(cls, http_client=None):
        url = f'{cls.BASE_URL}current'
        http_client = get_client(http_client)

        response = http_client.get(url)

        if response.status_code == 200:
            data = response.json()
            return cls.from_response(data, http_client)

        raise AgoraException('Could not get the current user')

    @classmethod
    def get_or_create(cls, username, password, email=None, first_name=None, last_name=None, is_superuser=False, http_client=None):
        http_client = get_client(http_client)
        url = cls.BASE_URL

        data = cls.get_list({'username': username})
        for user in data:
            if user.username == username:
                return user, True

        data = {
            'username': username,
            'password': password,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_superuser': is_superuser,
        }

        response = http_client.post(url, data, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                new_user = User.from_response(data, http_client)
                return new_user, False

        raise AgoraException('Could not create the user')

    def delete(self):
        raise AgoraException("Can't delete user via the python interface")

    def __str__(self):
        return f"User {self.id}: {self.username}"
