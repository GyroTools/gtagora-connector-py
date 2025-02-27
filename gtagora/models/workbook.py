import json

from gtagora.models.base import BaseModel
import base64
import numpy as np


class Workbook(BaseModel):
    BASE_URL = '/api/v2/workbook/'

    MASK_TYPE_EMPTY = 0
    MASK_TYPE_FILLED = 1
    MASK_TYPE_BITMASK1 = 2
    MASK_TYPE_BITMASK2 = 3
    MASK_TYPE_BITMASK3 = 4
    MASK_TYPE_BYTE_ARRAY = 5
    MASK_TYPE_REGULAR1 = 6
    MASK_TYPE_REGULAR2 = 7
    MASK_TYPE_REGULAR3 = 8

    def decode_masks(self):
        decoded_masks = {}
        if hasattr(self, 'mask'):
            masks = self.mask.get('mMasks')
            if masks:
                for mask in masks:
                    siz = [mask.get('mSizeX', 1), mask.get('mSizeY', 1), mask.get('mSizeZ', 1), mask.get('mSizeT', 1)]
                    name = mask.get('name', 'mask')
                    slice_masks = mask.get('mSliceMask')
                    if len(slice_masks) != siz[2] * siz[3]:
                        raise Exception('Invalid mask size')

                    cur_decoded_mask = np.zeros((siz[0], siz[1], siz[2]*siz[3]), dtype=np.uint8)
                    for i, slice_mask in enumerate(slice_masks):
                        decoded_list = self._decode_mask(slice_mask.get('mBase64Values', ''), siz[0]*siz[1])
                        cur_decoded_mask[:, :, i] = np.array(decoded_list).reshape(siz[0], siz[1])
                    cur_decoded_mask.reshape(siz)
                    decoded_masks[name] = cur_decoded_mask.reshape(siz)
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

    def _decode_mask(self, b64mask, length):
        encoded_mask = base64.b64decode(b64mask)

        mask = [0] * length
        if encoded_mask:
            mask_type = encoded_mask[0]
            nr_bytes, shifts = self._get_nr_bytes(mask_type)

            if mask_type == self.MASK_TYPE_EMPTY:
                return mask
            elif mask_type == self.MASK_TYPE_FILLED:
                return [encoded_mask[1]] * length
            elif mask_type == self.MASK_TYPE_BYTE_ARRAY:
                return list(encoded_mask[1:length + 1])
            elif mask_type in [self.MASK_TYPE_BITMASK1, self.MASK_TYPE_BITMASK2, self.MASK_TYPE_BITMASK3]:
                label = encoded_mask[1]
                target_index = int.from_bytes(encoded_mask[2:5], byteorder='big')
                source_index = 5
                entries = (len(encoded_mask) - 5) // nr_bytes

                values = encoded_mask[source_index:]
                run_lengths_target_inds = [0] * entries
                for i in range(entries):
                    for b in range(nr_bytes):
                        shift = shifts[b]
                        run_lengths_target_inds[i] += values[i * nr_bytes + b] << shift

                for i in range(0, len(run_lengths_target_inds), 2):
                    run_length = run_lengths_target_inds[i]
                    target_index_increment = run_lengths_target_inds[i + 1] if i + 1 < len(
                        run_lengths_target_inds) else 0
                    mask[target_index:target_index + run_length] = [label] * run_length
                    target_index += run_length + target_index_increment

            elif mask_type in [self.MASK_TYPE_REGULAR1, self.MASK_TYPE_REGULAR2, self.MASK_TYPE_REGULAR3]:
                target_index = 0
                label = encoded_mask[1]
                run_length = int.from_bytes(encoded_mask[2:5], byteorder='big')
                source_index = 5
                mask[target_index:target_index + run_length] = [label] * run_length
                target_index += run_length
                step = nr_bytes + 1
                entries = (len(encoded_mask) - 5) // step

                values = encoded_mask[source_index:]
                for i in range(entries):
                    label = values[i * step]
                    run_length = 0
                    for b in range(nr_bytes):
                        shift = shifts[b]
                        run_length += values[i * step + b + 1] << shift
                    mask[target_index:target_index + run_length] = [label] * run_length
                    target_index += run_length

        return mask

    def _get_nr_bytes(self, mask_type):
        if mask_type in [self.MASK_TYPE_REGULAR2, self.MASK_TYPE_BITMASK2]:
            return 2, [8, 0]
        elif mask_type in [self.MASK_TYPE_REGULAR3, self.MASK_TYPE_BITMASK3]:
            return 3, [16, 8, 0]
        else:
            return 1, [0]
