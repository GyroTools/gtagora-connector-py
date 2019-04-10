import os.path
from copy import deepcopy

from gtagora.models.base import BaseModel


class Datafile(BaseModel):
    BASE_URL = '/api/v1/datafile/'

    def download(self, filename=None):
        if not filename:
            head, tail = os.path.split(self.rel_filename)
            filename = tail

        if os.path.isdir(filename):
            filename = os.path.join(filename, self.rel_filename)

        url = f'{self.BASE_URL}{self.id}/download/'
        self.http_client.download(url, filename)

        downloaded_file = deepcopy(self)
        downloaded_file.download_path = filename
        return downloaded_file

    def __str__(self):
        return f'{self.original_filename} {self.size}'
