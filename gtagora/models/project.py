from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.dataset import Dataset
from gtagora.models.folder import Folder
from gtagora.models.series import Series
from gtagora.utils import remove_illegal_chars

from pathlib import Path


class Project(BaseModel):
    BASE_URL = '/api/v2/project/'

    def set_name(self, name):
        url = self.BASE_URL + str(self.id) + '/'
        data = {"name": name}
        response = self.http_client.put(url, data)

        if response.status_code == 200:
            data = response.json()
            self._set_values(data)
            return self
        else:
            raise AgoraException('Could not set the project name {0}', response.status_code)

    def get_exams(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/exam/?limit=10000000000'
        return self._get_object_list(url, filters, Series)

    def get_root_folder(self):
        return Folder.get(self.root_folder, http_client=self.http_client)

    @property
    def display_name(self):
        if self.is_myagora:
            return 'My Agora'
        else:
            return self.name

    def __str__(self):
        return f"Project: {self.get_display_name()}"
