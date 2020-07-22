from gtagora.exception import AgoraException
from gtagora.http.client import Client
from gtagora.http.connection import ApiKeyConnection, TokenConnection
from gtagora.models.dataset import Dataset
from gtagora.models.exam import Exam
from gtagora.models.project import Project
from gtagora.models.series import Series
from gtagora.models.folder import Folder
from gtagora.models.patient import Patient
from gtagora.models.user import User
from gtagora.models.group import Group
from gtagora.models.task import Task
from gtagora.models.trash import Trash
from gtagora.models.import_package import import_data

import json
import urllib3
from pathlib import Path
from typing import List

from gtagora.models.version import Version
from gtagora.utils import validate_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Agora:
    long_timeout = 180
    verify_certificate = False

    default_client = None
    version: Version = None

    def __init__(self, client):
        self.http_client = client
        self.set_default_client(client)
        self.version = self.get_version()
        self.version.needs('6.0.0', error_message='The python interface needs Agora version 6.0.0 or higher. Please update Agora')
        self.import_directroy = self.import_directory # for backward-compatibility.

    @staticmethod
    def create(url, api_key=None, user=None, password=None, token=None):
        """Creates an Agora instance. Prefer this method over using the Agora constructor.

        To authenticate use either the api_key parameter or the user and password parameter.
        Avoid writing your password into python files! Use the API key instead since you can
        simply renew or disable it.

        Arguments:
            url {string} -- The base url of the Agora server (e.g "https://agora.mycompany.com")

        Keyword Arguments:
            api_key {string} -- The API key of  (default: {None})
            user {string} -- The username (default: {None})
            password {string} -- The password (default: {None})

        Returns:
            Agora -- The agora instance
        """
        url = validate_url(url)

        if api_key:
            connection = ApiKeyConnection(url, api_key=api_key, verify_certificate=Agora.verify_certificate)
            client = Client(connection=connection)
        elif token:
            connection = TokenConnection(url, verify_certificate=Agora.verify_certificate)
            client = Client(connection=connection)
            connection.token = token
        else:
            connection = TokenConnection(url, verify_certificate=Agora.verify_certificate)
            client = Client(connection=connection)
            connection.login(client, user, password)

        if not client.check_connection():
            raise AgoraException('Could not connect to the Agora server at ' + url)

        return Agora(client)

    @staticmethod
    def set_default_client(client):
        Agora.default_client = client

    def ping(self):
        """Pings Agora and tests the connection

        Returns:
            bool -- True if the connection was successful.
        """
        url = '/api/v1/version/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return 'server' in data

        return False

    # Project
    def get_projects(self, filters=None):
        return Project.get_list(filters, http_client=self.http_client)

    def get_project(self, project_id):
        return Project.get(project_id, http_client=self.http_client)

    def get_myagora(self):
        return Project.get('myagora', http_client=self.http_client)

    # Folder
    def get_root_folder(self):
        """Returns a list of all root folder of the current user.

        Returns:
            List[Folder] -- The list of root folders
        """
        return self.get_myagora().get_root_folder()

    def get_folder(self, folder_id: int):
        """Returns the folder instance

        Arguments:
            folder_id {int} -- The ID of the folder to be retrieved

        Returns:
            Folder -- The folder
        """
        return Folder.get(folder_id, http_client=self.http_client)

    def get_or_create_folder(self, folder_path: Path, base_folder: Folder = None):
        """Creates a path in the base folder (base_folder_id).

        Arguments:
            folder_path {Path} -- A path to be created.

        Keyword Arguments:
            base_folder {Folder} -- The of the base folder. If None the root_folder is assumed. (default: {None})

        Returns:
            Folder -- Returns the last created folder
        """
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

    def get_exam(self, exam_id: int):
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
    def upload(self, paths: List[Path], target_folder_id: Folder = None, json_import_file: Path = None, wait=True,
               progress=False, relations: dict =None):
        """Upload and import files to Agora

        Arguments:
            paths {List[Path]} -- A list of files or directories to upload (default: {None})

        Keyword Arguments:
            target_folder {Folder} -- The destination folder (default: {None})
            json_import_file {Path} -- The path to a JSON import file. Will be used only in special cases.
                                       (default: {None})
            wait {bool} -- Wait until the full upload has been finished (default: {True})
            progress {bool} -- Show a progress (default: {False})

        Returns:
            [type] -- [description]
        """
        if relations:
            self.version.needs('6.3.0', 'relations')

        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.as_posix())

        return import_data(self.http_client, paths=paths, target_folder_id=target_folder_id,
                           json_import_file=json_import_file, wait=wait, progress=progress, relations=relations)

    def import_directory(self, directory: Path, target_folder_id: int = None, json_import_file: Path = None, wait=True,
                         progress=False, relations: dict =None):
        """Upload and import a directory to Agora.

        The directory sturcture of all subdirectries will be preserved.

        Arguments:
            directory {Path} -- A single directory to upload

        Keyword Arguments:
            target_folder {Folder} -- [description] (default: {None})
            json_import_file {Path} -- [description] (default: {None})
            wait {bool} -- [description] (default: {True})
            progress {bool} -- [description] (default: {False})
        """
        if directory is None or not isinstance(directory, Path) or directory.is_dir is False:
            raise TypeError("Expects a pathlib.Path for directory")

        if directory.exists is False:
            raise FileNotFoundError("Directory doesn't exists")

        return import_data(self.http_client, paths=[directory], target_folder_id=target_folder_id, json_import_file=json_import_file, wait=wait, progress=progress, relations=relations)

    # User
    def get_users(self):
        """Returns a list of all Agora users

        Returns:
            List[User] -- The list of users
        """
        return User.get_list(http_client=self.http_client)

    def get_current_user(self):
        """Returns the current user

        Returns:
            User -- The user object of the current user
        """
        return User.get_current_user(http_client=self.http_client)

    def get_groups(self):
        """Returns a list of all gropus

        Returns:
            List[Group] -- A list of a groups
        """
        return Group.get_list(http_client=self.http_client)

    def get_api_key(self, create=False):
        """Returns the API Key of the current user

        Keyword Arguments:
            create {bool} -- Creates a new API key even if there is a already an API key (default: {False})

        Raises:
            AgoraException: [description]

        Returns:
            [type] -- [description]
        """
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

    def get_version(self):
        """Returns the Agora version

        Returns:
            Version -- A Version object
        """
        return Version.get(http_client=self.http_client)

    def get_version(self):
        """Returns the Agora version

        Returns:
            Version -- A Version object
        """
        return Version.get(http_client=self.http_client)

    def close(self):
        pass
