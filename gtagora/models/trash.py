from gtagora.models.base import BaseModel


class Trash(BaseModel):

    BASE_URL = '/api/v1/trash/'

    def get_items(self, project_id):
        items = self.get_list(http_client=self.http_client)
        return [i for i in items if i.project == project_id]

    def empty(self, project_id):
        items = self.get_items(project_id)
        for item in items:
            url = f'{self.BASE_URL}{item.id}/delete'
            response = self.http_client.delete(url, timeout=60)
            if response.status_code != 204:
                print(f'Could not delete item with id = {item.id}')



