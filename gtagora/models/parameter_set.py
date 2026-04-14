from typing import Dict, List, Union

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.parameter import Parameter


class ParameterSet(BaseModel):
    BASE_URL = '/api/v2/parameterset/'

    def __init__(self, http_client):
        super().__init__(http_client)

    @classmethod
    def create(cls, http_client, parent_url: str, name: str, parameters: List[Dict]) -> 'ParameterSet':
        """Create a new user-defined ParameterSet on the parent object.

        Args:
            http_client: The HTTP client to use.
            parent_url: The parametersets endpoint URL of the parent object,
                e.g. '/api/v2/exam/1/parametersets/'.
            name: Name for the new ParameterSet.
            parameters: List of parameter dicts with at least 'Name' and 'Value' keys.

        Returns:
            The created ParameterSet instance.
        """
        data = {'name': name, 'parameters': parameters}
        response = http_client.post(parent_url, json=data)
        if response.status_code == 201:
            created = response.json()
            return cls.get(created['id'], http_client=http_client)
        raise AgoraException(
            f'Could not create ParameterSet. HTTP status = {response.status_code}: {response.text}'
        )

    @classmethod
    def update(cls, http_client, parameterset_id: int, name: str, parameters: List[Dict]) -> 'ParameterSet':
        """Update an existing user-defined ParameterSet.

        Args:
            http_client: The HTTP client to use.
            parameterset_id: The ID of the ParameterSet to update.
            name: New name for the ParameterSet.
            parameters: New list of parameter dicts with at least 'Name' and 'Value' keys.

        Returns:
            The updated ParameterSet instance.
        """
        url = f'{cls.BASE_URL}{parameterset_id}/'
        data = {'name': name, 'parameters': parameters}
        response = http_client.patch(url, json=data)
        if response.status_code == 200:
            return cls.get(parameterset_id, http_client=http_client)
        raise AgoraException(
            f'Could not update ParameterSet. HTTP status = {response.status_code}: {response.text}'
        )

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
