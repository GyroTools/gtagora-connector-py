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


class Agora:
    mLongTimeout = 180
    mVerifyCertificate = False

    def __init__(self, connection):
        self.connection = connection
        self.http_client = Client(connection)
        # if connection:
        # uri = urlparse(connection.mURL)
        # connection.mURL = uri.scheme
        # if uri.port:
        #     connection.mURL += ':' + uri.port
        #     self.connection = connection
        # else:
        #     self.connection = Connection(url, api_key=api_key, user=user, password=password)
        #     # Check if we can connect to the agora server (also checks credentials)
        #     IsConnection, ErrorMessage = gtAgoraRequest.check_connection(self.connection.mURL, self.connection)
        #     if not IsConnection:
        #         raise AgoraException('Could not connect to Agora: ' + ErrorMessage)

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

        return Agora(connection)

    def ping(self):

        url = '/api/v1/version/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return 'server' in data

        return False

    # Folder
    def get_root_folder(self):
        return Folder.get(0, self.http_client)

    def get_folder(self, folder_id):
        return Folder.get(folder_id, self.http_client)

    def get_patients(self, filters=None):
        # Check the connection(Because afterwards we increase the timeout time for the query and we want to make sure 
        # we have a connection)
        # if not self.http_client.check_connection():
        #     raise AgoraException('Could not connect to Agora: ')

        return Patient.get_list(self.http_client, filters)

    def get_patient(self, patient_id):
        return Patient.get(patient_id, self.http_client)

    # Exam
    def get_exams(self, filters=None):
        return Exam.get_list(self.http_client, filters)

    def get_exam(self, exam_id):
        return Exam.get(exam_id, self.http_client)

    # def SetExamName(self, aExamID, aName):
    #     if not isinstance( aExamID, int ):
    #         raise AgoraException('The exam ID must be numeric')

    #     vURL = self.mConnection.mURL + '/api/v1/exam/' + str(aExamID) + '/'
    #     vData = {"name": aName}
    #     Response = gtAgoraRequest.put(vURL, vData, self.mConnection)

    #     if 'id' in Response:
    #         return Exam(Response, self.mConnection)
    #     else:
    #         raise AgoraException('Could not set the exam name')

    # Series
    def get_series(self, filters=None):
        return Series.get_list(self.http_client, filters)

    def get_serie(self, series_id):
        return Series.get(series_id, self.http_client)

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

    # Import a directory or a list of files with optional target files
    def import_data(self, files, target_files=None, json_import_file=None, progress=False):
        import_package = ImportPackage(self.http_client).create()
        
        if isinstance(files, str) and os.path.isdir(files):
            return import_package.upload_directory(files, progress)
        else:
            return import_package.upload(files, target_files, json_import_file=json_import_file,
                                        progress=progress)

    def get_users(self):
        return User.get_list(self.http_client)

    def get_current_user(self):
        return User.get_current_user(self.http_client)

    def get_groups(self):
        return Group.get_list(self.http_client)
