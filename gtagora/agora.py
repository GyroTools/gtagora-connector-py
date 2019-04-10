import os

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
from gtagora.models.import_package import ImportPackage
from gtagora.utils import to_path_array


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
            connection = ApiKeyConnection(url, api_key=api_key)
            client = Client(connection=connection)
        else:
            connection = TokenConnection(url)
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

    # Search
    def search(self, aSearchString):
        Series = []

        if aSearchString and not isinstance(aSearchString, str):
            raise AgoraException('The search string must be a string')

        # Check the connection(Because afterwards we increase the timeout time for the query and we want to make sure we have a connection)
        IsConnection, ErrorMessage = gtAgoraRequest.check_connection(self.connection.mURL, self.connection)
        if not IsConnection:
            raise AgoraException('Could not connect to Agora: ' + ErrorMessage)

        vURL = self.connection.mURL + '/api/v1/serie/search/?q=' + aSearchString + '&limit=10000000000'
        Response = gtAgoraRequest.get(vURL, self.connection,
                                      gtAgora.mLongTimeout)

        if 'results' in Response and 'count' in Response:
            Results = Response['results']
            if Response['count'] == 0:
                return Series
            if Response['count'] != len(Results):
                print('Warning: Could not get all series')

            for curSeries in Results:
                Series.append(gtAgoraSeries(curSeries, self.connection))

            return Series
        else:
            raise AgoraException('Could not get the series')

    #
    def import_data(self, files, target_folder=None, target_files=None, json_import_file=None, wait=True,
                    progress=False):
        """
        Import a directory or a list of files with optional target file names.

        The target folder is optional. If
        target_folder is None and data is uploaded that can't be trated as an exam or series a new folder in the
        root will be created.

        :param files: One directroy or multiple files as string or Path
        :param target_folder: The target folder
        :param wait: Wait until the upload and import process ha sbeen finished
        :returns: The import package. Can be used to watch the upload
        """
        files = to_path_array(files)

        if not files:
            return None

        for f in files:
            if not f.exists():
                raise FileNotFoundError(f.as_posix())

        import_package = ImportPackage(http_client=self.http_client).create()
        
        if len(files) == 1 and files[0].is_dir():
            import_package.upload_directory(files[0],
                                            target_folder_id=target_folder.id,
                                            wait=wait,
                                            progress=progress)
        else:
            if not all([f.is_file() for f in files]):
                raise Exception('''Can not upload a list of files and directories. Only one directroy or multiple 
files are supported''')

            import_package.upload(files,
                                  target_folder_id=target_folder.id,
                                  target_files=target_files,
                                  json_import_file=json_import_file,
                                  wait=wait,
                                  progress=progress)
        return import_package

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

    def close(self):
        pass