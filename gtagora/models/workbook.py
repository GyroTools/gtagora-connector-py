from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel

from workbook.mask import DecodedMask, decode_full_mask  # noqa: F401 (re-exported)
from workbook.session import merge_contour_session, merge_mask_session
from workbook.session import resolve_contour_buttons as _resolve_contour_buttons
from workbook.templates import new_cmr_workbook_body


class Workbook(BaseModel):
    BASE_URL = '/api/v2/workbook/'

    def decode_masks(self):
        """Returns {mask name: DecodedMask} for every mask in this workbook - see
        workbook.mask.DecodedMask for how to turn one into a numpy array."""
        decoded_masks = {}
        if hasattr(self, 'mask'):
            masks = self.mask.get('mMasks')
            if masks:
                for mask in masks:
                    name = mask.get('name', 'mask')
                    decoded_masks[name] = decode_full_mask(mask)
        return decoded_masks

    @staticmethod
    def create(dataset_id: int, http_client):
        # TODO create different workbook types
        body = Workbook._new(dataset_id)
        url = Workbook.BASE_URL
        response = http_client.post(url, json=body)
        if response.status_code == 201:
            data = response.json()
            return Workbook.from_response(data, http_client)
        else:
            raise Exception('Could not create workbook: ' + str(response.status_code))

    @staticmethod
    def _new(dataset_id: int):
        return {
                  "id": None,
                  "dataset": dataset_id,
                  "name": "Workbook 1",
                  "locked": False,
                  "contour_tab": True,
                  "mask_tab": True,
                  "statistics_tab": True,
                  "cmr_tab": False,
                  "contour": {
                    "contourGroups": [],
                    "landmarkGroups": [],
                    "objectButtons": [
                      {
                        "mObjectType": "region_of_interest",
                        "mButtonLabel": "2D ROI",
                        "mTimeMode": 0,
                        "mObjectColor": {"r": 230, "g": 63, "b": 65},
                        "mCollapsedView": False,
                        "mContourGroupMode": 0,
                        "mContourMaskLabel": 1,
                        "id": 0
                      }
                    ]
                  },
                  "mask": {"mMasks": []}
                }

    @staticmethod
    def create_cmr(dataset_id: int, http_client, name: str = 'CMR Workbook'):
        """Creates a new CMR-flavoured workbook for a dataset (contour_tab, mask_tab,
        statistics_tab and cmr_tab all enabled), pre-populated with the default CMR
        contour/landmark buttons (LV EpiCard/EndoCard, RV EpiCard/EndoCard, PeriCard,
        Scar, Reference, RV insertion landmarks) - see
        workbook.templates.new_cmr_workbook_body.
        """
        body = new_cmr_workbook_body(dataset_id, name)
        response = http_client.post(Workbook.BASE_URL, json=body)
        if response.status_code != 201:
            raise AgoraException(f'Could not create the workbook: status={response.status_code}, {response.text}')
        return Workbook.from_response(response.json(), http_client)

    def resolve_contour_buttons(self) -> list:
        """Returns this workbook's existing contour buttons, or the default CMR set
        if it doesn't have any yet (e.g. a plain ROI/GENERIC workbook) - see
        workbook.session.resolve_contour_buttons.
        """
        return _resolve_contour_buttons(getattr(self, 'contour', None))

    def update(self, mask: dict = None, contour_groups: list = None, object_buttons: list = None) -> 'Workbook':
        """Merges a mask and/or contour groups into this workbook and PATCHes it back
        to Agora. Any existing mask/contour group sharing a name with an incoming one
        is replaced in place rather than duplicated, so calling update() again with
        the same mask/group names updates them instead of piling up duplicates - see
        workbook.session.merge_mask_session/merge_contour_session.

        mask: a single Mask dict (see workbook.mask.encode_mask for building slice
            data) to insert/replace by its 'name'. Omit to leave the mask session
            untouched.
        contour_groups: ContourGroup dicts to insert/replace by their 'name'. Omit
            (along with object_buttons) to leave the contour session untouched.
        object_buttons: replaces the workbook's objectButtons list outright - pass
            resolve_contour_buttons() (plus any new buttons) if you want to keep the
            existing ones. Required if contour_groups is given.
        """
        mask_session = getattr(self, 'mask', None) or {'id': self.id, 'mMasks': [], 'selectedMask': None}
        if mask is not None:
            mask_session = merge_mask_session(mask_session, self.id, mask)
        else:
            mask_session['id'] = self.id

        contour_session = getattr(self, 'contour', None) or \
            {'id': self.id, 'contourGroups': [], 'landmarkGroups': [], 'objectButtons': []}
        if contour_groups is not None or object_buttons is not None:
            contour_session = merge_contour_session(
                contour_session, self.id, contour_groups or [],
                object_buttons if object_buttons is not None else contour_session.get('objectButtons', []))
        else:
            contour_session['id'] = self.id

        url = f'{Workbook.BASE_URL}{self.id}/'
        response = self.http_client.patch(url, json={'mask': mask_session, 'contour': contour_session})
        if response.status_code != 200:
            raise AgoraException(f'Could not update the workbook: status={response.status_code}, {response.text}')
        return Workbook.from_response(response.json(), self.http_client)
