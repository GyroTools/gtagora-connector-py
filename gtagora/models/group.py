from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class Group(BaseModel):
    BASE_URL = '/api/v1/groups/'

    # def create(self, username, email=None, first_name=None, last_name=None):
    #     url = self.BASE_URL
        
    #     data = {
    #         'username': username,
    #         'email': email,
    #         'first_name': first_name,
    #         'last_name': last_name
    #     }

    #     response = self.http_client.post(url, data, timeout=60)
    #     if response.status_code == 201:
    #         data = response.json()
    #         if 'id' in data:
    #             self._set_values(data)
    #             return self

    #     raise AgoraException('Could not create the user')

    def delete(self):
        raise AgoraException("Can't delete group via the python interface")

    def __str__(self):
        return f"Group {self.id}: {self.name}"
