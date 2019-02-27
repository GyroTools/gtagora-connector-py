import datetime
import os
import time

from gtagora.models.base import BaseModel
from gtagora.exception import AgoraException


class ImportPackage(BaseModel):
    mTaskInfoTimeout = 120
    BASE_URL = '/api/v1/import/'

    def __init__(self, http_client):
        super().__init__(http_client)

    def create(self):
        url = self.BASE_URL
        response = self.http_client.post(url, data={}, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                self._set_values(data)
                return self
        raise AgoraException("Can't create an Import object")

    def upload(self, input_files, target_files=None, json_import_file=None, progress=False):

        # if json_import_file:
        #     if json_import_file not in InputFiles:
        #         raise Exception("The json_import_file must be included in the TargetFiles array as well")

        url = '/api/v1/import/' + str(self.id) + '/upload/'
        response = self.http_client.Upload(url, input_files, target_files, progress)

        url = '/api/v1/import/' + str(self.id) + '/complete/'
        if json_import_file:
            post_data = {
                'import_file': json_import_file
            }
        else:
            post_data = {}
        print(post_data)
        response = self.http_client.post(url, post_data, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if not 'state' in data:
                raise AgoraException(f'Could not get the task info: {data}')

            if not data['state'] == 2:
                Response = self.PollTaskInfo(data['id'])
                if data and Response['state'] == 2:
                    data = Response['data']
                    series = data['series']
                    url = '/api/v1/serie/' + str(series['id'])
                    Response = gtAgoraRequest.get(vURL, self.http_client)
                    if 'id' in Response:
                        return Series(Response, self.http_client)
                    else:
                        raise AgoraException('Could not get the series')

    def UploadDirectory(self, PathToDirectory, progress=False):
        InputFiles = []
        TargetFiles = []
        for root, dirs, files in os.walk(PathToDirectory):
            for f in files:
                vAbsoluteFilePath = os.path.join(root, f)
                InputFiles.append(vAbsoluteFilePath)
                TargetFiles.append(os.path.relpath(vAbsoluteFilePath, PathToDirectory).replace('\\', '/'))
        return self.Upload(InputFiles, TargetFiles, json_import_file=None, progress=progress)


class TaskInfo:
    def poll(self, task_id):
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < gtAgoraImport.mTaskInfoTimeout:
            vURL = self.http_client.mURL + '/api/v1/taskinfo/' + str(TaskID)
            Response = gtAgoraRequest.get(vURL, self.http_client, 60)
            if not 'state' in Response:
                raise AgoraException('Could not get the task info')

            if Response['state'] == 0 or Response['state'] == 1:
                time.sleep(2)
                continue
            elif Response['state'] == 2:
                return Response
            elif Response['state'] == 3:
                raise AgoraException(Response['error'])
            elif Response['state'] == 4 or Response['state'] == 5:
                return None

        raise AgoraException('Timeout while getting the task info')
