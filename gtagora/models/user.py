from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class User(BaseModel):
    BASE_URL = '/api/v1/user/'

    @classmethod
    def get_current_user(cls, http_client):
        
        url = f'{cls.BASE_URL}current'
        response = http_client.get(url)

        if response.status_code == 200:
            data = response.json()
            return cls.from_response(data, http_client)

        raise AgoraException('Could not get the current user')

    def get_or_create(self, username, email=None, first_name=None, last_name=None):
        url = self.BASE_URL
        
        response = self.get_list(self.http_client, {'username': username})
        if response.status_code == 200:
            data = response.json()
            for user in data:
                if user['username'] == username:
                    self._set_values(data)
                    return self, True

        data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }

        response = self.http_client.post(url, data, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                self._set_values(data)
                return self, False

        raise AgoraException('Could not create the user')

    def delete(self):
        raise AgoraException("Can't delete user via the python interface")

    def __str__(self):
        return f"User {self.id}: {self.username}"
