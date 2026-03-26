import pytest

from gtagora.exception import AgoraException
from gtagora.models.exam import Exam
from gtagora.models.folder import Folder
from gtagora.models.folder_item import FolderItem
from tests.helper import FakeResponse, load_fixture


class TestFolder:

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('folder/folder.json')))

        folder = Folder.get(5, http_client=http_client)

        assert isinstance(folder, Folder)
        assert folder.id == 5
        assert folder.name == 'Results'
        assert folder.project == 3
        assert folder.locked is False

    def test_get_uses_v2_url(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('folder/folder.json')))
        Folder.get(5, http_client=http_client)

        assert http_client.requests[-1]['url'] == '/api/v2/folder/5/'

    def test_get_items(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('folder/folder_items.json')))
        folder = Folder.from_response(load_fixture('folder/folder.json'), http_client=http_client)

        items = folder.get_items()

        assert len(items) == 2
        assert all(isinstance(i, FolderItem) for i in items)
        assert items[0].content_type == 'exam'
        assert isinstance(items[0].object, Exam)
        assert items[0].object.name == 'Brain MRI'
        assert items[1].content_type == 'folder'
        assert isinstance(items[1].object, Folder)
        assert items[1].object.name == 'Subfolder'
        assert http_client.requests[-1]['url'] == '/api/v1/folder/5/items/?limit=10000000000'

    def test_get_failure(self, http_client):
        http_client.set_next_response(FakeResponse(404, {}))

        with pytest.raises(AgoraException):
            Folder.get(999, http_client=http_client)
