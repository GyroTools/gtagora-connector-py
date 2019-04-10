import os

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel, LinkToFolderMixin
from gtagora.models.datafile import Datafile
from gtagora.models.parameter import Parameter


class DatasetType:
    NONE = 0
    PHILIPS_RAW = 100
    PHILIPS_REC = 101
    BRUKER_RAW = 200
    BRUKER_SUBJECT = 201
    BRUKER_IMAGE = 202
    DICOM = 300
    SIEMENS_RAW = 400
    DICOM = 1000
    OTHER = 100000


class Dataset(LinkToFolderMixin, BaseModel):
    BASE_URL = '/api/v1/dataset/'

    def _set_values(self, model_dict):
        for key, value in model_dict.items():
            if key == 'datafiles':
                datafiles = []
                for item in model_dict['datafiles']:
                    datafiles.append(Datafile.from_response(item,
                                                            http_client=self.http_client))
                setattr(self, key, datafiles)
            else:
                setattr(self, key, value)

    def get_datafiles(self):
        if hasattr(self, 'datafiles'):
            return self.datafiles
        else:
            return []

    def download(self, filename=None):
        datafiles = self.get_datafiles()
        downloaded_files = []
        for datafile in datafiles:
            downloaded_files.append(datafile.download(filename))
        return downloaded_files

    def get_parameter(self, filter=None):

        if filter and not isinstance(filter, str):
            raise AgoraException('The filter must be a string (e.g. ''description__name=EX_'')')

        if filter:
            filter = '&' + filter
        else:
            filter = ''

        # Check the connection(Because afterwards we increase the timeout time for the query and we want to make sure
        # we have a connection)
        if not self.http_client.check_connection():
            raise AgoraException('Could not connect to Agora')

        url = f'{self.BASE_URL}{self.id}/parameters/?limit=10000000000' + filter
        response = self.http_client.get(url, timeout=self.mLongTimeout)

        if response.status_code == 200:
            data = response.json()

            if 'results' in data and 'count' in data:
                parameters = []
                results = data['results']
                if data['count'] == 0:
                    return parameters
                if data['count'] != len(results):
                    print('Warning: Could not get all parameter')

                for parameter in results:
                    parameters.append(Parameter(parameter))

                return parameters

        raise AgoraException('Could not get the series')

    def create(self, series_id=None, exam_id=None, folder_id=None, type=DatasetType.OTHER):
        url = Dataset.BASE_URL
        if series_id:
            data = {"serie": series_id, "type": type}
        elif exam_id:
            data = {"exam": exam_id, "type": type}
        elif folder_id:
            data = {"folder": folder_id, "type": type}
        else:
            raise AgoraException('Please specify a SeriesID, ExamID or FolderID')

        response = self.http_client.post(url, json=data, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                self._set_values(data)
                return self

        raise AgoraException('Could not create the dataset')

    @classmethod
    def upload_files(cls, http_client, input_files, target_files, series_id=None, exam_id=None, folder_id=None,
                       dataset_type=DatasetType.OTHER):
        if (not series_id and not folder_id and not exam_id):
            raise AgoraException('Please specify a SeriesID, ExamID or FolderID')

        if isinstance(input_files, str):
            Files = []
            Files.append(input_files)
        else:
            Files = input_files

        if not target_files:
            target_files = [os.path.basename(file) for file in Files]

        if len(target_files) < len(Files):
            raise AgoraException('TargetFiles list too short.')

        for curFile in Files:
            if not os.path.isfile(curFile):
                raise AgoraException('File does not exist: ' + curFile)

        dataset = Dataset(http_client=http_client)
        dataset.create(series_id=series_id, exam_id=exam_id, folder_id=folder_id, type=dataset_type)
        url = f'/api/v1/dataset/{dataset.id}/upload/'
        if http_client.upload(url, input_files, target_files):
            return Dataset.get(dataset.id, http_client)

        raise AgoraException("Failed to create a new dataset")

    def __str__(self):
        return f"Dataset: {self.name}, {self.total_size}"
