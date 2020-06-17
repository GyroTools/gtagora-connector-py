from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel, LinkToFolderMixin, DownloadDatasetMixin
from gtagora.models.dataset import Dataset
from gtagora.models.series import Series
from gtagora.utils import remove_illegal_chars

from pathlib import Path


class Exam(LinkToFolderMixin, DownloadDatasetMixin, BaseModel):
    BASE_URL = '/api/v1/exam/'

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

        series = self.get_series()
        datasets = []
        for s in series:
            datasets += s.get_datasets(filters)

        datasets += self.get_files()

        return datasets

    def get_files(self):
        files = []

        url = f'{self.BASE_URL}{self.id}/files/?limit=10000000000'
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()

            if 'results' in data and 'count' in data:
                results = data['results']
                if data['count'] == 0:
                    return files
                if data['count'] != len(results):
                    print('Warning: Could not get all files')

                for curFile in results:
                    files.append(Dataset(curFile, http_client=self.http_client))

            return files

        raise AgoraException('Could not get the series')

    def upload(self, input_files, target_files=None):
        if target_files and len(input_files) != len(target_files):
            raise AgoraException("The Inputfiles and TargetFiles must have the same length")

        if isinstance(input_files, str):
            files = []
            files.append(input_files)
        else:
            files = input_files

        datasets = []
        for index, currrent_file in enumerate(files):
            cur_target_file = None
            if target_files:
                cur_target_file = target_files[index]
            datasets.append(self.http_client.upload_dataset(currrent_file, cur_target_file, self.http_client,
                                                            exam_id=self.id))
        return datasets

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

    def __str__(self):
        return f"Exam: {self.name}"
