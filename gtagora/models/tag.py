from gtagora.models.base import BaseModel
from gtagora.models.project import Project


class Tag(BaseModel):

    BASE_URL = '/api/v2/tag-definition/'

    def create(self, name, user: int=None, project=None, group: str = None, color: str = None):
        if user is None and project is None:
            raise ValueError('Either user or project must be set')

        data = {'label': name}
        data['user'] = user

        if isinstance(project, int):
            data['project'] = project
        elif isinstance(project, Project):
            data['project'] = project.id
        else:
            raise ValueError('Project must be an integer or a Project object')

        data['group'] = group
        data['color'] = color
        data['visibility'] = 2 if project is not None else 1
        data['scope'] = 1 if project is not None else 2

        response = self.http_client.post(self.BASE_URL, json=data)
        if response.status_code == 201:
            return Tag.from_response(response.json(), http_client=self.http_client)
        else:
            return None


class TagInstance(BaseModel):

    BASE_URL = '/api/v2/tag-instance/'


class RatingInstance(BaseModel):

    BASE_URL = '/api/v2/rating/'
