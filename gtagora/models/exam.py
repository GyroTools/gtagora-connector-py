from typing import List

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel, LinkToFolderMixin, DownloadDatasetMixin, TagMixin, RatingMixin, RelationMixin
from gtagora.models.dataset import Dataset
from gtagora.models.import_package import import_data
from gtagora.models.series import Series
from gtagora.models.timeline import TimelineItem
from gtagora.utils import remove_illegal_chars

from pathlib import Path


class Exam(LinkToFolderMixin, DownloadDatasetMixin, TagMixin, RatingMixin, RelationMixin, BaseModel):
    BASE_URL = '/api/v1/exam/'
    BASE_URL_V2 = '/api/v2/exam/'

    def set_name(self, name):
        url = self.BASE_URL + str(self.id) + '/'
        data = {"name": name}
        response = self.http_client.put(url, data)

        if response.status_code == 200:
            data = response.json()
            self._set_values(data)
            return self
        else:
            raise AgoraException('Could not set the exam name {0}', response.status_code)

    def get_series(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/series/?limit=10000000000'
        return self._get_object_list(url, filters, Series)

    def get_datasets(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        # the api/v1/files returns all datafiles in the exams (including series)
        url = f'{self.BASE_URL}{self.id}/files/?limit=10000000000'
        return self._get_object_list(url, filters, Dataset)

    def get_files(self):
        # the api/v2/datasets only returns the datasets which directly belongs to the exam
        url = f'{self.BASE_URL_V2}{self.id}/datasets/?limit=10000000000'
        return self._get_object_list(url, None, Dataset)

    def upload(self, paths: List[Path], verbose=False):
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.as_posix())
        return import_data(self.http_client, paths=paths, exam_id=self.id, wait=False, verbose=verbose)

    def download(self, target_path: Path):
        for series in self.get_series():
            for dataset in series.get_datasets():
                final_path = target_path / remove_illegal_chars(self.name) / remove_illegal_chars(series.name)
                final_path.mkdir(parents=True, exist_ok=True)
                dataset.download(final_path)
        for dataset in self.get_files():
            final_path = target_path / self.name
            final_path.mkdir(parents=True, exist_ok=True)
            dataset.download(final_path)

    def upload_dataset(self, input_files, dataset_type, target_files=None):
        # This function creates a dataset of a given type all files given as input will be added to one dataset.
        # Please note: At the moment there is no consistency check. We could create datasets with improper
        # files (e.g. a PAR/REC dataset without PAR/REC files)
        return self.http_client.upload_dataset(input_files, target_files, self.http_client, exam_id=self.id,
                                               dataset_type=dataset_type)

    def copy_to_project(self, project_id):
        url = f'{self.BASE_URL_V2}{self.id}/copy_to/{project_id}/'
        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not copy the exam: status = {response.status_code}')

        return self._get_new_exam_from_timeline(response)

    def copy_to_folder(self, target_folder_id):
        from gtagora.models.folder import Folder
        folder_url = f'{Folder.BASE_URL}{target_folder_id}/'
        response = self.http_client.get(folder_url, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not find the folder with id = {target_folder_id}')
        folder = Folder.from_response(response.json(), self.http_client)
        if folder.project == self.project:
            url = f'{self.BASE_URL_V2}{self.id}/link_to/{target_folder_id}/'
        else:
            url = f'{self.BASE_URL_V2}{self.id}/copy_to/{folder.project}/folder/{target_folder_id}/'

        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code >= 400:
            raise AgoraException(f'Could not copy the exam: status = {response.status_code}, message = {response.text}')

        return self._get_new_exam_from_timeline(response) if folder.project != self.project else self

    def move_to_project(self, project_id, target_folder_id=None):
        if not target_folder_id:
            url = f'{self.BASE_URL_V2}{self.id}/move_to{project_id}/'
        else:
            url = f'{self.BASE_URL_V2}{self.id}/move_to/{project_id}/folder/{target_folder_id}/'

        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not move the exam: status = {response.status_code}')

        return self._get_new_exam_from_timeline(response)

    def lock(self):
        url = f'{self.BASE_URL_V2}lock_ids/'
        body = {"ids": [self.id]}
        response = self.http_client.post(url, body)
        if response.status_code != 200:
            raise AgoraException(f'Could not lock the exam: status = {response.status_code}')

        self.locked = True
        return self

    def unlock(self):
        url = f'{self.BASE_URL_V2}unlock_ids/'
        body = {"ids": [self.id]}
        response = self.http_client.post(url, body)
        if response.status_code != 200:
            raise AgoraException(f'Could not unlock the exam: status = {response.status_code}')

        self.locked = True
        return self

    def __str__(self):
        return f"Exam: {self.name}"

    def _get_new_exam_from_timeline(self, response):
        timeline_item = TimelineItem.from_response(response.json(), self.http_client)
        timeline_item = timeline_item.poll()
        related_objects = timeline_item.data.get('related_objects')
        if related_objects:
            for obj in related_objects:
                if  obj.get('id') and obj.get('id') != self.id:
                    try:
                        return self.get(obj.get('id'), self.http_client)
                    except:
                        pass

        return None

