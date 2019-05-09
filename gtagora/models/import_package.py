import datetime
import os
import time
import tempfile
import zipfile
from pathlib import Path

from gtagora.models.base import BaseModel
from gtagora.exception import AgoraException
from gtagora.utils import ZipUploadFiles


class ImportPackage(BaseModel):
    mTaskInfoTimeout = 120
    BASE_URL = '/api/v1/import/'

    def __init__(self, http_client=None):
        super().__init__(http_client=http_client)
        self.last_progress = None
        self.zip_upload = False

    def create(self):
        url = self.BASE_URL
        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                self._set_values(data)
                return self
        raise AgoraException("Can't create an Import object")

    def upload(self, input_files, target_files=None, target_folder_id=None, json_import_file=None, wait=True,
               timeout=None, progress=False):

        base_url = '/api/v1/import/' + str(self.id) + '/'
        url = base_url + 'upload/'

        if self._check_zip_option(input_files):
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_upload = ZipUploadFiles(input_files, target_files)
                input_files, target_files = zip_upload.create_zip(temp_dir)
                response = self.http_client.upload(url, input_files, target_files, progress=progress)
        else:
            self.zip_upload = False
            response = self.http_client.upload(url, input_files, target_files, progress=progress)

        if self.complete(json_import_file, target_folder_id=target_folder_id):
            if wait:
                start_time = datetime.datetime.now()
                while (datetime.datetime.now() - start_time).seconds < timeout if timeout else True:
                    data = self.progress()
                    if data['state'] == 5 or data['state'] == -1:
                        return data
                    time.sleep(5)

        raise AgoraException(f'Failed to complete upload {self.id}: {response.status_code}')

    def complete(self, json_import_file=None, target_folder_id=None):
        url = self.BASE_URL + str(self.id) + '/complete/'
        post_data = {}
        if json_import_file:
            post_data.update({'import_file': json_import_file})
        if target_folder_id:
            post_data.update({'folder': target_folder_id})

        response = self.http_client.post(url, json=post_data)
        if response.status_code == 204:
            return True
        raise AgoraException(f'fail to get progress from ImportPackage {self.id}: {response.status_code}')

    def progress(self):
        url = self.BASE_URL + str(self.id) + '/progress/'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'state' not in data:
                raise AgoraException(f'Could not get the task info: {data}')
            self.last_progress = data
            return self.last_progress
        raise AgoraException(f'fail to get progress from ImportPackage {self.id}: {response.status_code}')

    def get_objects(self):
        url = self.BASE_URL + str(self.id) + '/get_objects/'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        raise AgoraException(f'fail to get object from ImportPackage {self.id}: {response.status_code}')

    def upload_directory(self, path: Path, target_folder_id=None, wait=True, progress=False):
        input_files = []
        target_files = []

        for root, dirs, files in os.walk(path):
            for f in files:
                absolute_file_path = Path(root, f)
                input_files.append(absolute_file_path.as_posix())
                target_files.append(absolute_file_path.relative_to(path.parent).as_posix())

        return self.upload(input_files,
                           target_files=target_files,
                           target_folder_id=target_folder_id,
                           json_import_file=None,
                           wait=wait,
                           progress=progress)

    def _check_zip_option(self, input_files):
        return len(input_files) > 5

