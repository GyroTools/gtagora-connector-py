from pathlib import Path
from typing import List

from gtagora.exception import AgoraException
from gtagora.models.base import LinkToFolderMixin, BaseModel, DownloadDatasetMixin, SearchMixin, TagMixin, RatingMixin, \
    RelationMixin
from gtagora.models.dataset import Dataset
from gtagora.models.import_package import import_data
from gtagora.models.timeline import TimelineItem


class Series(LinkToFolderMixin, DownloadDatasetMixin, TagMixin, RatingMixin, RelationMixin, SearchMixin, BaseModel):
    BASE_URL = '/api/v1/serie/'
    BASE_URL_V2 = '/api/v2/series/'

    def get_datasets(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/datasets/?limit=10000000000'
        return self._get_object_list(url, filters, Dataset)

    def upload(self, paths: List[Path], verbose=False):
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.as_posix())
        return import_data(self.http_client, paths=paths, series_id=self.id, wait=False, verbose=verbose)

    def upload_dataset(self, input_files, dataset_type, target_files=None):
        # This function creates a dataset of a given type all files given as input will be added to one dataset.
        # Please note: At the moment there is no consistency check. We could create datasets with improper
        # files (e.g. a PAR/REC dataset without PAR/REC files)
        return self.http_client.upload_dataset(input_files, target_files, serie_id=self.id, dataset_type=dataset_type)

    def get_parameter(self, name):
        datasets = self.get_datasets()
        for dataset in datasets:
            par = dataset.get_parameter(name)
            if par:
                return par

    def get_parameters(self, filter: str = None):
        datasets = self.get_datasets()
        pars = []
        for dataset in datasets:
            par = dataset.get_parameters(filter=filter)
            if par:
                pars.extend(par)
        pars = list({p.Name: p for p in pars}.values())
        return pars

    def copy_to_folder(self, target_folder_id):
        from gtagora.models.folder import Folder
        folder_url = f'{Folder.BASE_URL}{target_folder_id}/'
        response = self.http_client.get(folder_url, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not find the folder with id = {target_folder_id}')
        folder = Folder.from_response(response.json(), self.http_client)
        url = f'{self.BASE_URL_V2}{self.id}/copy_to/{folder.project}/folder/{target_folder_id}/'
        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not copy the series: status = {response.status_code}')

        return self._get_new_series_from_timeline(response)

    def __str__(self):
        return f"Series: {self.name}"

    def _get_new_series_from_timeline(self, response):
        timeline_item = TimelineItem.from_response(response.json(), self.http_client)
        timeline_item = timeline_item.poll()
        if not timeline_item.data:
            return None

        related_objects = timeline_item.data.get('related_objects')
        if related_objects:
            for obj in related_objects:
                if obj.get('id') and obj.get('id') != self.id:
                    try:
                        return self.get(obj.get('id'), self.http_client)
                    except:
                        pass

        return None
