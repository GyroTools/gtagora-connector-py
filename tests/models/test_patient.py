from gtagora.models.patient import Patient
from tests.helper import FakeResponse
from tests.models import data


class TestPatient:

    def test_init(self, http_client):
        p = Patient(http_client=http_client)
        assert p

    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, data.patient))

        p = Patient.get(12, http_client=http_client)

        assert isinstance(p, Patient)
        assert p.id == 1
        assert p.name == "Daniel Smith"

    def test_get_list(self, http_client):
        http_client.set_next_response(FakeResponse(200, data.patient_list))

        patient_list = Patient.get_list(http_client=http_client)

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
