import pytest

from gtagora.exception import AgoraException
from gtagora.models.exam import Exam
from gtagora.models.series import Series
from tests.helper import FakeResponse, load_fixture


class TestExam:

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('exam/exam.json')))

        exam = Exam.get(1, http_client=http_client)

        assert isinstance(exam, Exam)
        assert exam.id == 1
        assert exam.name == 'Brain MRI'
        assert exam.patient == 2
        assert exam.project == 3
        assert exam.locked is False

    def test_get_list(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('exam/exam_list.json')))

        exams = Exam.get_list(http_client=http_client)

        assert len(exams) == 2
        assert exams[0].id == 1
        assert exams[1].id == 2
        assert exams[1].name == 'Spine MRI'

    def test_get_series(self, http_client):
        http_client.set_next_response(FakeResponse(200, load_fixture('series/series_list.json')))
        exam = Exam.from_response(load_fixture('exam/exam.json'), http_client=http_client)

        series = exam.get_series()

        assert len(series) == 2
        assert all(isinstance(s, Series) for s in series)
        assert series[0].name == 'T1 MPRAGE'
        assert series[1].name == 'T2 FLAIR'
        last = http_client.requests[-1]
        assert last['url'] == '/api/v1/exam/1/series/?limit=10000000000'

    def test_set_name(self, http_client):
        updated = load_fixture('exam/exam.json')
        updated['name'] = 'Renamed Exam'
        http_client.set_next_response(FakeResponse(200, updated))
        exam = Exam.from_response(load_fixture('exam/exam.json'), http_client=http_client)

        result = exam.set_name('Renamed Exam')

        assert result.name == 'Renamed Exam'
        last = http_client.requests[-1]
        assert last['method'] == 'PUT'
        assert last['url'] == '/api/v1/exam/1/'

    def test_set_name_failure(self, http_client):
        http_client.set_next_response(FakeResponse(400, {}))
        exam = Exam.from_response(load_fixture('exam/exam.json'), http_client=http_client)

        with pytest.raises(AgoraException):
            exam.set_name('Bad Name')

    def test_get_failure(self, http_client):
        http_client.set_next_response(FakeResponse(404, {}))

        with pytest.raises(AgoraException):
            Exam.get(999, http_client=http_client)
