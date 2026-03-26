import pytest

from gtagora.exception import AgoraException
from gtagora.models.dataset import Dataset
from gtagora.models.series import Series
from tests.helper import FakeResponse, load_fixture


class TestSeries:

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('series/series.json')))

        series = Series.get(1, http_client=http_client)

        assert isinstance(series, Series)
        assert series.id == 1
        assert series.name == 'T1 MPRAGE'
        assert series.exam == 1
        assert series.acquisition_number == 1
        assert series.locked is False

    def test_get_list(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('series/series_list.json')))

        series_list = Series.get_list(http_client=http_client)

        assert len(series_list) == 2
        assert series_list[0].id == 1
        assert series_list[1].id == 2
        assert series_list[1].name == 'T2 FLAIR'

    def test_get_datasets(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('dataset/dataset_list.json')))
        series = Series.from_response(load_fixture('series/series.json'), http_client=http_client)

        datasets = series.get_datasets()

        assert len(datasets) == 2
        assert all(isinstance(d, Dataset) for d in datasets)
        assert datasets[0].name == 'DICOM dataset'
        assert datasets[1].type == 600
        last = http_client.requests[-1]
        assert last['url'] == '/api/v1/serie/1/datasets/?limit=10000000000'

    def test_get_failure(self, http_client):
        http_client.set_next_response(FakeResponse(404, {}))

        with pytest.raises(AgoraException):
            Series.get(999, http_client=http_client)
