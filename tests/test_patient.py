from mock import patch

from gtagora.http.client import Client
from gtagora.http.connection import BasicConnection
from gtagora.models.patient import Patient


class FakeResponse:

    def __init__(self, status_code=200, data={}):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class FakeClient(Client):
    def __init__(self, connection, response=FakeResponse()):
        super().__init__(connection)
        self.response = response

    def check_connection(self):
        return True

    def get(self, url, timeout=None, params=None, **kwargs):
        return self.response


class TestPatient:

    def test_init(self):
        connection = BasicConnection('http://localhost', 'test', 'test')
        http_client = FakeClient(connection)
        p = Patient(http_client)
        assert p

    def test_get(self):
        connection = BasicConnection('http://localhost', 'test', 'test')

        expected_patient = {
            "id": 1,
            "permissions": {
                "write": True,
                "read": True
            },
            "most_recent_exam_date": "2016-04-21T13:43:13Z",
            "created_date": "2016-10-11T12:46:13Z",
            "modified_date": "2018-11-22T06:48:24Z",
            "name": "Daniel Smith",
            "patient_id": "HOSP2",
            "birth_date": "1980-12-05",
            "sex": "m",
            "weight": 72,
            "anonymous": False,
            "creator": None
        }

        http_client = FakeClient(connection, response=FakeResponse(200, expected_patient))
        p = Patient(http_client)
        p = Patient.get(12, http_client)

        assert isinstance(p, Patient)
        assert p.id == 1
        assert p.name == "Daniel Smith"

    def test_get_list(self):
        connection = BasicConnection('http://localhost', 'test', 'test')

        get_data = {
            "count": 6,
            "limit": 10,
            "offset": 0,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T13:43:13Z",
                    "created_date": "2016-10-11T12:46:13Z",
                    "modified_date": "2018-11-22T06:48:24Z",
                    "name": "Daniel Smith",
                    "patient_id": "HOSP2",
                    "birth_date": "1980-12-05",
                    "sex": "m",
                    "weight": 72,
                    "anonymous": False,
                    "creator": None
                },
                {
                    "id": 2,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T10:58:16Z",
                    "created_date": "2016-10-11T12:57:32Z",
                    "modified_date": "2018-04-03T15:09:33Z",
                    "name": "Marcel Hoppe",
                    "patient_id": "HOSP1",
                    "birth_date": "1974-03-07",
                    "sex": "m",
                    "weight": 80,
                    "anonymous": False,
                    "creator": None
                },
                {
                    "id": 3,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T12:26:11Z",
                    "created_date": "2016-10-11T12:59:03Z",
                    "modified_date": "2016-10-28T12:31:37Z",
                    "name": "Stefan Meier",
                    "patient_id": "HOSP4",
                    "birth_date": "1976-12-08",
                    "sex": "m",
                    "weight": 71,
                    "anonymous": False,
                    "creator": None
                },
            ]
        }

        http_client = FakeClient(connection)

        with patch.object(http_client, 'get') as mocked_get:
            mocked_get.return_value = FakeResponse(200, get_data)

            p = Patient(http_client)
            patient_list = Patient.get_list(http_client)

            assert len(patient_list) == 3
            p = patient_list[0]
            assert p.id == 1
            assert p.name == "Daniel Smith"

            p = patient_list[1]
            assert p.id == 2
            assert p.name == "Marcel Hoppe"

            p = patient_list[2]
            assert p.id == 3
            assert p.name == "Stefan Meier"
