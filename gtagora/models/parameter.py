from gtagora.exception import AgoraException


class Parameter:
    def __init__(self, http_client):
        # if 'is_favorite' not in model_dict:
        #     raise AgoraException('Could not initialize the Parameter: is_favorite is missing')

        # self.http_client = http_client
        # for key, value in model_dict.items():
        #     setattr(self, key, value)

        super().__init__(http_client)
