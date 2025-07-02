from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.parameter import Parameter


class ParameterSet(BaseModel):
    BASE_URL = '/api/v2/parameterset/'

    def __init__(self, http_client):
        super().__init__(http_client)

    def _get_object(self, id):
        if id:
            url = f'{self.BASE_URL}{id}/?flat=True'
        else:
            url = f'{self.BASE_URL}'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return self.__class__.from_response(data, http_client=self.http_client)

        raise AgoraException('Could not get the {0}. HTTP status = {1}'.format(self.__class__.__name__, response.status_code))

    def get_parameters(self):
        return Parameter.get_list_from_data(self.parameters) if hasattr(self, 'parameters') else []

    def get_parameter(self, name):
        if hasattr(self, 'parameters'):
            parameter = next((x for x in self.parameters if x.get('Name') == name), None)
            return Parameter.from_response(parameter) if parameter else None
        return None

    @staticmethod
    def diff(list1, list2):
        dict1 = {p.Name: p.Value for p in list1}
        dict2 = {p.Name: p.Value for p in list2}

        only_in_1 = set(dict1) - set(dict2)
        only_in_2 = set(dict2) - set(dict1)
        in_both = set(dict1) & set(dict2)

        diffs = {
            "only_in_list1": {name: dict1[name] for name in only_in_1},
            "only_in_list2": {name: dict2[name] for name in only_in_2},
            "different_values": {name: (dict1[name], dict2[name]) for name in in_both if dict1[name] != dict2[name]},
        }
        return diffs
