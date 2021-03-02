from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class Host(BaseModel):
    def copy_to_project(self, project_id):
        url = f'/api/v2/project/{project_id}/host/'
        data = self.to_dict()
        response = self.http_client.post(url, json=data, timeout=60)

        if response.status_code != 201:
            raise AgoraException(f'Cannot copy the task: status = {response.status_code}')

    def move_to_project(self, project_id):
        url = f'/api/v2/project/{project_id}/host/{self.id}/move/'
        response = self.http_client.post(url, json={}, timeout=60)

        if response.status_code != 200:
            raise AgoraException(f'Cannot copy the task: status = {response.status_code}')