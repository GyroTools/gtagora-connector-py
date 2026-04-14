import pytest

from gtagora.exception import AgoraException
from gtagora.models.dataset import Dataset
from gtagora.models.exam import Exam
from gtagora.models.folder import Folder
from gtagora.models.parameter_set import ParameterSet
from gtagora.models.patient import Patient
from gtagora.models.series import Series
from tests.helper import FakeResponse, load_fixture


PARAMETERSET_LIST_URL = '/api/v2/exam/1/parametersets/'
# ParameterSet._get_object appends ?flat=True
PARAMETERSET_10_URL = '/api/v2/parameterset/10/?flat=True'
PARAMETERSET_11_URL = '/api/v2/parameterset/11/?flat=True'
PARAMETERSET_20_URL = '/api/v2/parameterset/20/?flat=True'


class TestParametersMixin:

    # ------------------------------------------------------------------
    # get_parametersets
    # ------------------------------------------------------------------

    def test_get_parametersets_returns_list(self, http_client):
        parameterset_full = load_fixture('parameterset/parameterset.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, load_fixture('parameterset/parameterset_list.json')))
        http_client.set_response(PARAMETERSET_10_URL, FakeResponse(200, parameterset_full))
        http_client.set_response(PARAMETERSET_11_URL, FakeResponse(200, {'id': 11, 'name': 'DICOM Parameters', 'read_only': True}))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        parametersets = exam.get_parametersets()

        assert len(parametersets) == 2
        assert all(isinstance(ps, ParameterSet) for ps in parametersets)

    def test_get_parametersets_empty(self, http_client):
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, []))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        parametersets = exam.get_parametersets()

        assert parametersets == []

    def test_get_parametersets_failure_raises(self, http_client):
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(403, {}))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)

        with pytest.raises(AgoraException):
            exam.get_parametersets()

    # ------------------------------------------------------------------
    # set_parameters — create path (no existing user parameterset)
    # ------------------------------------------------------------------

    def test_set_parameters_creates_when_no_existing(self, http_client):
        created = load_fixture('parameterset/parameterset_created.json')
        # GET list → empty
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, []), method='GET')
        # POST → 201 created
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(201, created), method='POST')
        # GET after creation
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.set_parameters({'TR': 1.5}, name='User Parameters')

        assert isinstance(result, ParameterSet)
        post_requests = [r for r in http_client.requests if r['method'] == 'POST']
        assert any(PARAMETERSET_LIST_URL in r['url'] for r in post_requests)

    def test_set_parameters_payload_contains_correct_keys(self, http_client):
        created = load_fixture('parameterset/parameterset_created.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, []), method='GET')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(201, created), method='POST')
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        exam.set_parameters({'TR': 1.5, 'TE': 0.03}, name='My Set')

        post_req = next(r for r in http_client.requests if r['method'] == 'POST')
        assert post_req['data']['name'] == 'My Set'
        assert {'Name': 'TR', 'Value': 1.5} in post_req['data']['parameters']
        assert {'Name': 'TE', 'Value': 0.03} in post_req['data']['parameters']

    def test_set_parameters_dict_converts_to_list(self):
        from gtagora.models.base import ParametersMixin
        result = ParametersMixin._normalise_parameters({'TR': 1.5, 'TE': 0.03})
        assert {'Name': 'TR', 'Value': 1.5} in result
        assert {'Name': 'TE', 'Value': 0.03} in result

    def test_set_parameters_list_passthrough(self):
        from gtagora.models.base import ParametersMixin
        raw = [{'Name': 'TR', 'Value': 1.5, 'Properties': {'unit': 'ms'}}]
        result = ParametersMixin._normalise_parameters(raw)
        assert result == raw

    # ------------------------------------------------------------------
    # set_parameters — update path (existing user parameterset found)
    # ------------------------------------------------------------------

    def test_set_parameters_updates_existing(self, http_client):
        """When a writable ParameterSet with the given name exists, PATCH is used."""
        parameterset_full = load_fixture('parameterset/parameterset.json')
        # List returns one writable parameterset with name "User Parameters"
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, load_fixture('parameterset/parameterset_list.json')))
        http_client.set_response(PARAMETERSET_10_URL, FakeResponse(200, parameterset_full))
        http_client.set_response(PARAMETERSET_11_URL, FakeResponse(200, {'id': 11, 'name': 'DICOM Parameters', 'read_only': True}))

        # After PATCH, a GET is issued to refresh the object
        updated = dict(parameterset_full)
        updated['parameters'] = [{'Name': 'TR', 'Value': 2.0}]
        http_client.set_next_response(FakeResponse(200, updated))  # PATCH response (not used)

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.set_parameters({'TR': 2.0}, name='User Parameters')

        assert isinstance(result, ParameterSet)
        patch_requests = [r for r in http_client.requests if r['method'] == 'PATCH']
        assert any(str(10) in r['url'] for r in patch_requests)

    def test_set_parameters_does_not_update_readonly(self, http_client):
        """A read-only ParameterSet with matching name should not be updated."""
        readonly_list = [{'id': 11, 'name': 'User Parameters', 'read_only': True}]
        readonly_full = {'id': 11, 'name': 'User Parameters', 'read_only': True}
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, readonly_list), method='GET')
        http_client.set_response(PARAMETERSET_11_URL, FakeResponse(200, readonly_full))

        created = load_fixture('parameterset/parameterset_created.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(201, created), method='POST')
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.set_parameters({'TR': 1.5}, name='User Parameters')

        assert isinstance(result, ParameterSet)
        post_requests = [r for r in http_client.requests if r['method'] == 'POST']
        assert any(PARAMETERSET_LIST_URL in r['url'] for r in post_requests)

    # ------------------------------------------------------------------
    # add_parameters — always creates
    # ------------------------------------------------------------------

    def test_add_parameters_always_creates(self, http_client):
        """add_parameters always POSTs even when a parameterset with the same name exists."""
        created = load_fixture('parameterset/parameterset_created.json')
        http_client.set_next_response(FakeResponse(201, created))
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.add_parameters({'TR': 1.5}, name='User Parameters')

        assert isinstance(result, ParameterSet)
        post_requests = [r for r in http_client.requests if r['method'] == 'POST']
        assert any(PARAMETERSET_LIST_URL in r['url'] for r in post_requests)

    def test_add_parameters_default_name(self, http_client):
        """add_parameters uses 'User Parameters' as default name."""
        created = load_fixture('parameterset/parameterset_created.json')
        http_client.set_next_response(FakeResponse(201, created))
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        exam.add_parameters({'TR': 1.5})

        post_req = next(r for r in http_client.requests if r['method'] == 'POST')
        assert post_req['data']['name'] == 'User Parameters'

    # ------------------------------------------------------------------
    # update_parameters — merges into existing
    # ------------------------------------------------------------------

    def test_update_parameters_preserves_existing(self, http_client):
        """update_parameters keeps untouched parameters intact."""
        parameterset_full = load_fixture('parameterset/parameterset.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, load_fixture('parameterset/parameterset_list.json')))
        http_client.set_response(PARAMETERSET_10_URL, FakeResponse(200, parameterset_full))
        http_client.set_response(PARAMETERSET_11_URL, FakeResponse(200, {'id': 11, 'name': 'DICOM Parameters', 'read_only': True}))

        updated = dict(parameterset_full)
        updated['parameters'] = [{'Name': 'TR', 'Value': 2.0}, {'Name': 'TE', 'Value': 0.03}]
        http_client.set_next_response(FakeResponse(200, updated))  # PATCH response

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.update_parameters({'TR': 2.0}, name='User Parameters')

        assert isinstance(result, ParameterSet)
        patch_req = next(r for r in http_client.requests if r['method'] == 'PATCH')
        sent_params = {p['Name']: p['Value'] for p in patch_req['data']['parameters']}
        # TR was updated
        assert sent_params['TR'] == 2.0
        # TE was preserved from the existing parameterset
        assert sent_params['TE'] == 0.03

    def test_update_parameters_adds_new_key(self, http_client):
        """update_parameters adds a brand-new parameter without removing existing ones."""
        parameterset_full = load_fixture('parameterset/parameterset.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, load_fixture('parameterset/parameterset_list.json')))
        http_client.set_response(PARAMETERSET_10_URL, FakeResponse(200, parameterset_full))
        http_client.set_response(PARAMETERSET_11_URL, FakeResponse(200, {'id': 11, 'name': 'DICOM Parameters', 'read_only': True}))

        updated = dict(parameterset_full)
        http_client.set_next_response(FakeResponse(200, updated))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        exam.update_parameters({'Flip': 90}, name='User Parameters')

        patch_req = next(r for r in http_client.requests if r['method'] == 'PATCH')
        sent_params = {p['Name']: p['Value'] for p in patch_req['data']['parameters']}
        assert sent_params['TR'] == 1.5    # existing preserved
        assert sent_params['TE'] == 0.03   # existing preserved
        assert sent_params['Flip'] == 90   # new key added

    def test_update_parameters_creates_when_no_existing(self, http_client):
        """update_parameters creates a new ParameterSet if none exists."""
        created = load_fixture('parameterset/parameterset_created.json')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(200, []), method='GET')
        http_client.set_response(PARAMETERSET_LIST_URL, FakeResponse(201, created), method='POST')
        http_client.set_response(PARAMETERSET_20_URL, FakeResponse(200, created))

        exam = Exam.from_response({'id': 1, 'name': 'Test Exam'}, http_client=http_client)
        result = exam.update_parameters({'TR': 1.5})

        assert isinstance(result, ParameterSet)
        post_requests = [r for r in http_client.requests if r['method'] == 'POST']
        assert any(PARAMETERSET_LIST_URL in r['url'] for r in post_requests)

    def test_merge_parameters_helper(self):
        """_merge_parameters correctly merges new values into existing parameters."""
        from gtagora.models.base import ParametersMixin
        from gtagora.models.parameter import Parameter

        existing = [
            Parameter.from_response({'Name': 'TR', 'Value': 1.5}),
            Parameter.from_response({'Name': 'TE', 'Value': 0.03}),
        ]
        new_params = [{'Name': 'TR', 'Value': 2.0}, {'Name': 'Flip', 'Value': 90}]

        merged = ParametersMixin._merge_parameters(existing, new_params)
        merged_dict = {p['Name']: p['Value'] for p in merged}

        assert merged_dict['TR'] == 2.0    # updated
        assert merged_dict['TE'] == 0.03   # preserved
        assert merged_dict['Flip'] == 90   # new

    # ------------------------------------------------------------------
    # Mixin is present on all expected classes
    # ------------------------------------------------------------------

    @pytest.mark.parametrize('cls', [Exam, Series, Patient, Dataset, Folder])
    def test_mixin_present_on_model_class(self, cls):
        from gtagora.models.base import ParametersMixin
        assert issubclass(cls, ParametersMixin)

