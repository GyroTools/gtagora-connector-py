import json
import os
import urllib3

from gtagora.models.trash import Trash
from gtagora.utils import _import_data

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from gtagora.exception import AgoraException
from gtagora.http.client import Client
from gtagora.http.connection import ApiKeyConnection, TokenConnection
from gtagora.models.dataset import Dataset
from gtagora.models.exam import Exam
from gtagora.models.series import Series
from gtagora.models.folder import Folder
from gtagora.models.patient import Patient
from gtagora.models.user import User
from gtagora.models.group import Group
from gtagora.models.task import Task


class Agora:
    long_timeout = 180
    verify_certificate = False

    default_client = None

    def __init__(self, client):
        self.http_client = client
        self.set_default_client(client)

    @staticmethod
    def create(url, api_key=None, user=None, password=None):
        if api_key:
            connection = ApiKeyConnection(url, api_key=api_key, verify_certificate=Agora.verify_certificate)
            client = Client(connection=connection)
        else:
            connection = TokenConnection(url, verify_certificate=Agora.verify_certificate)
            client = Client(connection=connection)
            connection.login(client, user, password)

        client.check_connection()
        return Agora(client)

    @staticmethod
    def set_default_client(client):
        Agora.default_client = client

    def ping(self):
        url = '/api/v1/version/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return 'server' in data

        return False

    # Folder
    def get_root_folder(self):
        return Folder.get(0, http_client=self.http_client)

    def get_folder(self, folder_id):
        return Folder.get(folder_id, http_client=self.http_client)

    def get_or_create_folder(self, folder_path, base_folder=None):

        if base_folder is None:
            base_folder = self.get_root_folder()

        return base_folder.get_or_create(folder_path)

    # Patient
    def get_patients(self, filters=None):
        return Patient.get_list(filters, http_client=self.http_client)

    def get_patient(self, patient_id):
        return Patient.get(patient_id, http_client=self.http_client)

    # Exam
    def get_exam_list(self, filters=None):
        return Exam.get_list(filters, http_client=self.http_client)

    def get_exam(self, exam_id):
        return Exam.get(exam_id, http_client=self.http_client)

    # Series
    def get_series_list(self, filters=None):
        return Series.get_list(filters, http_client=self.http_client)

    def get_series(self, series_id):
        return Series.get(series_id, http_client=self.http_client)

    def get_dataset(self, dataset_id):
        return Dataset.get(dataset_id, http_client=self.http_client)

    # Tasks
    def get_tasks(self):
        return Task.get_list(None, http_client=self.http_client)

    def get_task(self, task_id):
        return Task.get(task_id, http_client=self.http_client)

    def delete_task(self, task_id):
        url = f'{Task.BASE_URL}{task_id}/'
        response = self.http_client.delete(url, timeout=60)
        if response.status_code != 204:
            raise AgoraException('Cannot delete the task: ' + response.text)

    def export_tasks(self, file):
        url = Task.BASE_URL
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            for d in data:
                d.pop('context_help', None)

            with open(file, 'w') as outfile:
                json.dump(data, outfile)

    def import_tasks(self, file):
        tasks = self.load_tasks(file)
        for task in tasks:
            try:
                task.create()
            except AgoraException as e:
                print(f'Warning: Could not import the task {task.name}: {str(e)}')

    def load_tasks(self, file):
        with open(file) as json_file:
            data = json.load(json_file)
            return Task.get_list_from_data(data)


    # Search
    def search_series(self, aSearchString):
        return Series.search(aSearchString, self.http_client)

    # Import
    def import_data(self, files, target_folder=None, target_files=None, json_import_file=None, wait=True,
                    progress=False):
        return _import_data(self.http_client, files, target_folder, target_files, json_import_file, wait, progress)

    # User
    def get_users(self):
        return User.get_list(http_client=self.http_client)

    def get_current_user(self):
        return User.get_current_user(http_client=self.http_client)

    def get_groups(self):
        return Group.get_list(http_client=self.http_client)

    def get_api_key(self, create=False):
        response = self.http_client.get('/api/v1/apikey/')

        if response.status_code == 404 and create:
            response = self.http_client.post('/api/v1/apikey/', json={})

        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            return data

        raise AgoraException('Could not get the API key')


    # Trash
    def empty_trash(self):
        trash = Trash()
        trash.empty()


    def close(self):
        pass
