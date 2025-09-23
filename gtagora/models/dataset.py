import os

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel, LinkToFolderMixin, TagMixin, RatingMixin
from gtagora.models.datafile import Datafile
from gtagora.models.image_info import ImageInfo
from gtagora.models.parameter import Parameter
from gtagora.models.parameter_set import ParameterSet
from gtagora.models.workbook import Workbook


class DatasetType:
    NONE = 0
    PHILIPS_RAW = 100
    PHILIPS_PARREC = 101
    PHILIPS_SPECTRO = 102
    PHILIPS_EXAMCARD = 103,
    PHILIPS_SINFILE = 104,
    BRUKER_RAW = 200
    BRUKER_SUBJECT = 201
    BRUKER_IMAGE = 202
    DICOM = 300
    SIEMENS_RAW = 400
    SIEMENS_PRO = 401
    ISMRMRD = 500
    NIFTI1 = 600
    NIFTI2 = 601
    NIFTI_ANALYZE75 = 602
    JMRUI_SPECTRO = 700
    AEX = 800,
    QUERY = 10000
    OTHER = 100000

    def get_name(self, id: int) -> str:
        """Returns the name of the dataset type."""
        for attr in dir(self):
            if attr.isupper() and getattr(self, attr) == id:
                return attr
        return 'UNKNOWN'

    def get_id(self, name: str) -> int:
        """Returns the id of the dataset type."""
        name = name.upper()
        if hasattr(self, name):
            return getattr(self, name)
        else:
            raise AgoraException(f'Unknown dataset type: {name}')


class Dataset(LinkToFolderMixin, TagMixin, RatingMixin, BaseModel):
    BASE_URL = '/api/v1/dataset/'
    BASE_URL_V2 = '/api/v2/dataset/'

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

    def get_parametersets(self):
        url = f'{self.BASE_URL_V2}{self.id}/parametersets/'
        response = self.http_client.get(url)
        parametersets = []
        if response.status_code == 200:
            data = response.json()
            for parset in data:
                if 'id' in parset:
                    parametersets.append(ParameterSet.get(parset['id'], http_client=self.http_client))

        self.cached_parametersets = parametersets
        return parametersets

    def get_parameters(self, filter: str = None):
        if hasattr(self, 'parameters'):
            return self.filtered_parameters(filter)

        if hasattr(self, 'cached_parametersets'):
            parametersets = self.cached_parametersets
        else:
            parametersets = self.get_parametersets()
        parameters = []
        for parameterset in parametersets:
            parameters.extend(parameterset.get_parameters())

        self.parameters = parameters
        return self.filtered_parameters(filter)

    def filtered_parameters(self, filter):
        if hasattr(self, 'parameters') and filter is not None:
            return [p for p in self.parameters if filter in p.Name]
        else:
            return self.parameters

    def get_parameter(self, name):
        if hasattr(self, 'cached_parametersets'):
            parametersets = self.cached_parametersets
        else:
            parametersets = self.get_parametersets()

        for parameterset in parametersets:
            par = parameterset.get_parameter(name)
            if par:
                return par
        return None

    def get_info(self):
        url = f'{self.BASE_URL}{self.id}/image_info/'
        info = self._get_object_list(url, None, ImageInfo)
        return info if info else None

    def get_workbooks(self):
        url = f'{self.BASE_URL_V2}{self.id}/workbook/'
        workbooks = self._get_object_list(url, None, Workbook)
        if not workbooks:
            # create a new workbook if none exists
            new_workbook = Workbook.create(self.id, self.http_client)
            workbooks = [new_workbook]
        return workbooks if workbooks else None

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

    def copy_to_folder(self, target_folder_id):
        url = f'{self.BASE_URL_V2}{self.id}/copy_to_project/{target_folder_id}/'
        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not copy the dataset: status = {response.status_code}, message = {response.text}')
        return Dataset.from_response(response.json(), self.http_client)

    def __str__(self):
        return f"Dataset: {self.name}, {self.total_size}"
