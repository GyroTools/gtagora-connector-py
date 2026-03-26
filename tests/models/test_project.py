import pytest

from gtagora.exception import AgoraException
from gtagora.models.exam import Exam
from gtagora.models.project import Project
from tests.helper import FakeResponse, load_fixture


class TestProject:

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('project/project.json')))

        project = Project.get(3, http_client=http_client)

        assert isinstance(project, Project)
        assert project.id == 3
        assert project.name == 'Neuroscience Study'
        assert project.root_folder == 10
        assert project.exam_count == 5
        assert project.is_myagora is False

    def test_get_list(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('project/project_list.json')))

        projects = Project.get_list(http_client=http_client)

        assert len(projects) == 2
        assert projects[0].id == 3
        assert projects[1].id == 4
        assert projects[1].name == 'Cardiac Study'

    def test_display_name(self, http_client):
        project = Project.from_response(load_fixture('project/project.json'), http_client=http_client)
        assert project.display_name == 'Neuroscience Study'

    def test_display_name_myagora(self, http_client):
        data = load_fixture('project/project.json')
        data['is_myagora'] = True
        project = Project.from_response(data, http_client=http_client)
        assert project.display_name == 'My Agora'

    def test_get_exams(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('exam/exam_list.json')))
        project = Project.from_response(load_fixture('project/project.json'), http_client=http_client)

        exams = project.get_exams()

        assert len(exams) == 2
        assert all(isinstance(e, Exam) for e in exams)
        assert http_client.requests[-1]['url'] == '/api/v2/project/3/exam/?limit=10000000000'

    def test_set_name(self, http_client):
        updated = load_fixture('project/project.json')
        updated['name'] = 'Renamed Project'
        http_client.set_next_response(FakeResponse(200, updated))
        project = Project.from_response(load_fixture('project/project.json'), http_client=http_client)

        result = project.set_name('Renamed Project')

        assert result.name == 'Renamed Project'
        last = http_client.requests[-1]
        assert last['method'] == 'PUT'
        assert last['url'] == '/api/v2/project/3/'

    def test_get_failure(self, http_client):
        http_client.set_next_response(FakeResponse(404, {}))

        with pytest.raises(AgoraException):
            Project.get(999, http_client=http_client)
