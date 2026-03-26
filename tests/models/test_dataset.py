import pytest

from gtagora.exception import AgoraException
from gtagora.models.datafile import Datafile
from gtagora.models.dataset import Dataset
from tests.helper import FakeResponse, load_fixture


class TestDataset:

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('dataset/dataset.json')))

        dataset = Dataset.get(1, http_client=http_client)

        assert isinstance(dataset, Dataset)
        assert dataset.id == 1
        assert dataset.name == 'DICOM dataset'
        assert dataset.type == 300
        assert dataset.serie == 1
        assert dataset.total_size == 10485760

    def test_get_list(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('dataset/dataset_list.json')))

        datasets = Dataset.get_list(http_client=http_client)

        assert len(datasets) == 2
        assert datasets[0].id == 1
        assert datasets[1].id == 2
        assert datasets[1].type == 600

    def test_datafiles_parsed_from_response(self, http_client):
        dataset = Dataset.from_response(load_fixture('dataset/dataset.json'), http_client=http_client)

        datafiles = dataset.get_datafiles()

        assert len(datafiles) == 2
        assert all(isinstance(df, Datafile) for df in datafiles)
        assert datafiles[0].original_filename == 'scan_001.dcm'
        assert datafiles[1].size == 5242880

    def test_get_datafiles_empty_when_not_in_response(self, http_client):
        # dataset_list entries have no datafiles key with content
        data = load_fixture('dataset/dataset_list.json')['results'][0]
        dataset = Dataset.from_response(data, http_client=http_client)

        assert dataset.get_datafiles() == []

    def test_get_failure(self, http_client):
        http_client.set_next_response(FakeResponse(404, {}))

        with pytest.raises(AgoraException):
            Dataset.get(999, http_client=http_client)
