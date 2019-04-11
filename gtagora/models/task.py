import json

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class Task(BaseModel):

    BASE_URL = '/api/v1/taskdefinition/'

    def create(self):
        data = self.toDict()
        data['id'] = None
        if 'inputs' in data and data['inputs']:
            for input in data['inputs']:
                if 'id' in input:
                    input['id'] = None
        response = self.http_client.post(self.BASE_URL, json=data, timeout=60)
        if response.status_code != 201:
            raise AgoraException('Cannot create a task: ' + response.text)
        else:
            created_task = json.loads(response.content)
            result = self.get_list_from_data([created_task])
            return result[0] if result else None


    def save(self):
        if not hasattr(self, 'id') or not self.id:
            self.create()
        else:
            url = f'{self.BASE_URL}{self.id}/'
            data = self.toDict()
            response = self.http_client.put(url, json=data, timeout=60)
            if response.status_code != 200:
                raise AgoraException('Cannot create a task: ' + response.text)

    def delete(self):
        if not hasattr(self, 'id') or not self.id:
            raise AgoraException('Cannot delete the task: No ID available')
        else:
            url = f'{self.BASE_URL}{self.id}/'
            response = self.http_client.delete(url, timeout=60)
            if response.status_code != 204:
                raise AgoraException('Cannot delete the task: ' + response.text)

    def toDict(self):
        fields = ['container_name', 'container_options', 'execute_template', 'host', 'host_id', 'id', 'inputs', 'members', 'mount_volumes', 'name', 'outputs', 'parse_output_for_error', 'success_exit_code', 'task_target', 'use_docker']

        d = dict()
        for field in fields:
            d[field] = self.__dict__.get(field)

        return d
