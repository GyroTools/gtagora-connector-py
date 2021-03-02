from gtagora.exception import AgoraException
from gtagora.models.base import LinkToFolderMixin, BaseModel, DownloadDatasetMixin, SearchMixin
from gtagora.models.dataset import Dataset
from gtagora.models.timeline import TimelineItem


class Series(LinkToFolderMixin, DownloadDatasetMixin, BaseModel, SearchMixin):
    BASE_URL = '/api/v1/serie/'
    BASE_URL_V2 = '/api/v2/series/'

    def get_datasets(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/datasets/?limit=10000000000'
        return self._get_object_list(url, filters, Dataset)

    def upload(self, input_files, target_files=None):
        if target_files and len(input_files) != len(target_files):
            raise AgoraException("The Inputfiles and TargetFiles must have the same length")

        if isinstance(input_files, str):
            files = [input_files]
        else:
            files = input_files

        datasets = []
        for index, curFile in enumerate(files):
            cur_target_file = None
            if target_files:
                cur_target_file = target_files[index]
            datasets.append(Dataset.upload_files(self.http_client, curFile, cur_target_file, series_id=self.id))
        return datasets

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

    def search_parameter(self, search_string):
        datasets = self.get_datasets()
        pars = []
        for dataset in datasets:
            cur_pars = dataset.search_parameter(search_string)
            pars.extend(cur_pars)
        return pars

    def copy_to_folder(self, target_folder_id):
        url = f'{self.BASE_URL_V2}{self.id}/copy_to_project/{target_folder_id}/'
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
