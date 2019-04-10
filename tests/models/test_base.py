from gtagora import Agora
from gtagora.models.base import BaseModel
from tests.helper import FakeResponse


class TestBase:

    def test_get__default_client(self, http_client):
        Agora.set_default_client(http_client)
        expected_data = {
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

        http_client.set_next_response(FakeResponse(200, expected_data))

        p = BaseModel.get(12)

        assert isinstance(p, BaseModel)
        assert p.id == 1
        assert p.name == "Daniel Smith"