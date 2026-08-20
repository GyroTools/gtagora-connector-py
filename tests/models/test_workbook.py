import pytest

from gtagora.exception import AgoraException
from gtagora.models.workbook import DecodedMask, Workbook
from tests.helper import FakeResponse
from workbook.mask import encode_mask


class TestWorkbook:

    def test_create(self, http_client):
        http_client.set_next_response(FakeResponse(201, {'id': 5, 'dataset': 3, 'cmr_tab': False}))

        workbook = Workbook.create(3, http_client)

        assert isinstance(workbook, Workbook)
        assert workbook.id == 5
        assert workbook.cmr_tab is False

    def test_create_failure(self, http_client):
        http_client.set_next_response(FakeResponse(400, {}))

        with pytest.raises(Exception):
            Workbook.create(3, http_client)

    def test_create_cmr(self, http_client):
        http_client.set_next_response(FakeResponse(201, {'id': 5, 'dataset': 3, 'cmr_tab': True,
                                                          'contour': {'objectButtons': []}}))

        workbook = Workbook.create_cmr(3, http_client, name='My CMR')

        request = http_client.requests[-1]
        assert request['method'] == 'POST'
        assert request['data']['name'] == 'My CMR'
        assert request['data']['cmr_tab'] is True
        assert len(request['data']['contour']['objectButtons']) == 9  # 7 contour + 2 landmark buttons
        assert isinstance(workbook, Workbook)
        assert workbook.id == 5

    def test_create_cmr_failure(self, http_client):
        http_client.set_next_response(FakeResponse(400, {}))

        with pytest.raises(AgoraException):
            Workbook.create_cmr(3, http_client)

    def test_resolve_contour_buttons_returns_existing(self, http_client):
        workbook = Workbook.from_response(
            {'id': 1, 'contour': {'objectButtons': [{'mObjectType': 'lv_endocard', 'mContourGroupMode': 1}]}},
            http_client=http_client)

        assert workbook.resolve_contour_buttons() == workbook.contour['objectButtons']

    def test_resolve_contour_buttons_falls_back_to_cmr_defaults(self, http_client):
        workbook = Workbook.from_response({'id': 1, 'contour': {'objectButtons': []}}, http_client=http_client)

        buttons = workbook.resolve_contour_buttons()

        assert len(buttons) == 7
        assert buttons[0]['mObjectType'] == 'lv_epicard'

    def test_update_merges_mask_and_contour_groups_keeping_others(self, http_client):
        workbook = Workbook.from_response(
            {'id': 5, 'mask': {'mMasks': [{'name': 'Manual', 'id': 0}]},
             'contour': {'contourGroups': [{'name': 'Manual'}], 'objectButtons': []}},
            http_client=http_client)
        mask = {'name': 'AI Segmentation', 'mSizeX': 1, 'mSizeY': 1, 'mSizeZ': 1, 'mSizeT': 1,
                'mSliceMask': [{'mBase64Values': encode_mask([1])}]}
        contour_groups = [{'name': 'AI Segmentation', 'contourType': 'lv_endocard'}]
        buttons = [{'mObjectType': 'lv_endocard', 'mContourGroupMode': 1}]
        http_client.set_next_response(FakeResponse(200, {'id': 5}))

        workbook.update(mask=mask, contour_groups=contour_groups, object_buttons=buttons)

        request = http_client.requests[-1]
        assert request['method'] == 'PATCH'
        sent_mask_session = request['data']['mask']
        sent_contour_session = request['data']['contour']
        assert [m['name'] for m in sent_mask_session['mMasks']] == ['Manual', 'AI Segmentation']
        assert sent_mask_session['mMasks'][1]['id'] == 1  # next free id after 'Manual' (id 0)
        assert [g['name'] for g in sent_contour_session['contourGroups']] == ['Manual', 'AI Segmentation']
        assert sent_contour_session['objectButtons'] == buttons

    def test_update_replaces_existing_mask_and_group_by_name(self, http_client):
        workbook = Workbook.from_response(
            {'id': 5, 'mask': {'mMasks': [{'name': 'AI Segmentation', 'id': 3, 'old': True}]},
             'contour': {'contourGroups': [{'name': 'AI Segmentation', 'old': True}], 'objectButtons': []}},
            http_client=http_client)
        mask = {'name': 'AI Segmentation', 'new': True}
        contour_groups = [{'name': 'AI Segmentation', 'new': True}]
        http_client.set_next_response(FakeResponse(200, {'id': 5}))

        workbook.update(mask=mask, contour_groups=contour_groups, object_buttons=[])

        request = http_client.requests[-1]
        sent_mask_session = request['data']['mask']
        sent_contour_session = request['data']['contour']
        assert sent_mask_session['mMasks'] == [{'name': 'AI Segmentation', 'id': 3, 'new': True}]
        assert sent_contour_session['contourGroups'] == [{'name': 'AI Segmentation', 'new': True}]

    def test_update_failure(self, http_client):
        workbook = Workbook.from_response({'id': 5}, http_client=http_client)
        http_client.set_next_response(FakeResponse(400, {}))

        with pytest.raises(AgoraException):
            workbook.update(mask={'name': 'AI Segmentation'})

    def test_decode_masks(self, http_client):
        mask = {'name': 'AI Segmentation', 'mSizeX': 1, 'mSizeY': 1, 'mSizeZ': 1, 'mSizeT': 1,
                'mSliceMask': [{'mBase64Values': encode_mask([7])}]}
        workbook = Workbook.from_response({'id': 5, 'mask': {'mMasks': [mask]}}, http_client=http_client)

        decoded = workbook.decode_masks()

        assert isinstance(decoded['AI Segmentation'], DecodedMask)
        assert decoded['AI Segmentation'].data == [7]
        assert decoded['AI Segmentation'].shape == (1, 1, 1, 1)

    def test_decode_masks_empty_when_no_mask(self, http_client):
        workbook = Workbook.from_response({'id': 5}, http_client=http_client)

        assert workbook.decode_masks() == {}
