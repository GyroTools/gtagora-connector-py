import json

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.exam import Exam
from gtagora.models.folder import Folder
from gtagora.models.host import Host
from gtagora.models.project_role import ProjectRole
from gtagora.models.task import Task
from gtagora.models.trash import Trash


class Project(BaseModel):
    BASE_URL = '/api/v2/project/'

    ROLE_MANAGER = 1
    ROLE_SCIENTIST = 2
    ROLE_USER = 3
    ROLE_OBSERVER = 4

    PROJECT_ROLE = (
        (ROLE_MANAGER, 'manager'),
        (ROLE_SCIENTIST, 'scientist'),
        (ROLE_USER, 'user'),
        (ROLE_OBSERVER, 'observer')
        )

    def set_name(self, name):
        url = self.BASE_URL + str(self.id) + '/'
        data = {"name": name}
        response = self.http_client.put(url, data)

        if response.status_code == 200:
            data = response.json()
            self._set_values(data)
            return self
        else:
            raise AgoraException('Could not set the project name {0}', response.status_code)

    def get_exams(self, filters=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.BASE_URL}{self.id}/exam/?limit=10000000000'
        return self._get_object_list(url, filters, Exam)

    def get_tasks(self):
        url = f'{self.BASE_URL}{self.id}/task/?limit=10000000000'
        return self._get_object_list(url, None, Task)

    def import_tasks(self, file):
        with open(file) as json_file:
            data = json.load(json_file)

        url = f'{self.BASE_URL}{self.id}/task/imp/'
        response = self.http_client.post(url, json=data, timeout=60)
        if response.status_code != 200:
            raise AgoraException(f'Could not import the task: status = {response.status_code}')

    def get_hosts(self):
        url = f'{self.BASE_URL}{self.id}/host/?limit=10000000000'
        return self._get_object_list(url, None, Host)

    def get_root_folder(self):
        return Folder.get(self.root_folder, http_client=self.http_client)

    def add_member(self, user_id: int, role: int):
        role_id = None
        roles = self.get_roles()
        for r in roles:
            if r.id == role:
                role_id = r.id
                break
        if not role_id:
            raise AgoraException('Unknown role')

        url = f'/api/v2/projectmembership/'
        data = dict()
        data['project'] = self.id
        data['role'] = role_id
        data['user'] = user_id
        response = self.http_client.post(url, json=data, timeout=60)
        if response.status_code != 201:
            raise AgoraException(f'Could not add member: status = {response.status_code}')

    def copy_settings_from(self, other_project, copy_members=True, copy_tasks=True, copy_hosts=True):
        if copy_members:
            for membership in other_project.memberships:
                self.add_member(membership.get('user'), membership.get('role'))

        if copy_tasks:
            tasks = other_project.get_tasks()
            for task in tasks:
                task.copy_to_project(self.id)

        if copy_hosts:
            hosts = other_project.get_hosts()
            for host in hosts:
                host.copy_to_project(self.id)

    def get_roles(self):
        return self._get_object_list(ProjectRole.BASE_URL, None, ProjectRole)

    # Trash
    def empty_trash(self):
        trash = Trash()
        trash.empty(self.id)

    def get_tags(self, name=None):
        from gtagora.models.tag import Tag
        url = f'{self.BASE_URL}{self.id}/tag-definition/'
        tags = self._get_object_list(url, None, Tag)
        if name:
            tags = [t for t in tags if t.label == name]
        return tags

    @property
    def display_name(self):
        if self.is_myagora:
            return 'My Agora'
        else:
            return self.name

    def __str__(self):
        return f"Project: {self.get_display_name()}"
