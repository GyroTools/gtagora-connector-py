from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel, DownloadDatasetMixin
from gtagora.models.exam import Exam


class Patient(BaseModel, DownloadDatasetMixin):

    BASE_URL = '/api/v1/patient/'

    def get_exams(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/exams/?limit=10000000000'
        return self._get_object_list(url, filters, Exam)

    def get_series(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        series = []
        exams = self.get_exams()
        for exam in exams:
            series += exam.get_series(filters)

        return series

    def get_datasets(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        datasets = []
        series = self.get_series()
        for s in series:
            datasets += s.get_datasets(filters)

        return datasets
