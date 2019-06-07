import math
import os
import uuid

import requests

from gtagora.exception import AgoraException


class Client:
    TIMEOUT = 20
    UPLOAD_TIMEOUT = 60
    UPLOAD_CHUCK_SIZE = 100 * 1024 * 1024  # 100MB
    DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB

    def __init__(self, connection):
        self.connection = connection

    def check_connection(self):
        response = self.get('/api/v1/user/current/')
        if response.status_code == 200:
            data = response.json()
            return 'institution' in data

        return False

    def get(self, url, timeout=None, params=None, **kwargs):
        url = self.connection.url + url
        timeout = timeout if timeout else self.TIMEOUT
        auth = self.connection.get_auth()
        return requests.get(url, auth=auth, params=params, timeout=timeout,
                            verify=self.connection.verify_certificate, **kwargs)

    def post(self, url, data=None, json=None, timeout=None, params=None, **kwargs):
        url = self.connection.url + url
        timeout = timeout if timeout else self.TIMEOUT
        return requests.post(url, auth=self.connection.get_auth(), data=data, json=json, params=params, timeout=timeout,
                             verify=self.connection.verify_certificate, **kwargs)

    def put(self, url, json, timeout=None, params=None, **kwargs):
        url = self.connection.url + url
        timeout = timeout if timeout else self.TIMEOUT
        return requests.put(url, auth=self.connection.get_auth(), json=json, params=params, timeout=timeout,
                            verify=self.connection.verify_certificate, **kwargs)

    def delete(self, url, timeout=None, **kwargs):
        url = self.connection.url + url
        timeout = timeout if timeout else self.TIMEOUT
        return requests.delete(url, auth=self.connection.get_auth(), timeout=timeout,
                               verify=self.connection.verify_certificate, **kwargs)

    def download(self, url, target_filename):
        response = self.get(url, stream=True)
        if response.status_code == 200:
            with open(target_filename, 'wb') as file:
                for chunk in response.iter_content(self.DOWNLOAD_CHUNK_SIZE):
                    file.write(chunk)

    def upload(self, url, input_files, target_files=None, progress=False):
        response = self.get('/api/v1/version/')
        if response.status_code == 200:
            data = response.json()
            print(f"Ping {data}")
        else:
            print("Ping failed")

        if isinstance(input_files, str):
            files = []
            files.append(input_files)
        else:
            files = input_files

        if not target_files:
            target_files = [os.path.basename(file) for file in files]

        if len(target_files) < len(files):
            raise AgoraException('target_files list too short.')

        for index, cur_file in enumerate(files):
            print(f"Upload file: {cur_file} > {url}")

            if not os.path.isfile(cur_file):
                raise AgoraException('Could not open file ' + cur_file)

            filesize = os.path.getsize(cur_file)
            nof_chunks = math.ceil(filesize / self.UPLOAD_CHUCK_SIZE)

            head, tail = os.path.split(cur_file)
            filename = tail
            target_filename = target_files[index]

            uid = str(uuid.uuid4())

            with open(cur_file, mode='rb') as file:
                for chunk in range(0, nof_chunks):
                    if progress:
                        self.print_progress(index, len(files), chunk, nof_chunks)
                    data = file.read(self.UPLOAD_CHUCK_SIZE)
                    files = {'file': (filename, data)}
                    form = {
                        'description': '',
                        'flowChunkNumber': str(chunk),
                        'flowChunkSize': str(self.UPLOAD_CHUCK_SIZE),
                        'flowCurrentChunkSize': str(len(data)),
                        'flowTotalSize': str(filesize),
                        'flowIdentifier': uid,
                        'flowFilename': target_filename,
                        'flowRelativePath': target_filename,
                        'flowTotalChunks': str(nof_chunks)}
                    response = self.post(url, files=files, data=form, timeout=self.UPLOAD_TIMEOUT)
                    if response.status_code != 200:
                        raise AgoraException(
                            f"Failed to upload chunk {chunk} of file {cur_file}. Status code: {response.status_code}")

        print(f"Upload done")
        return True

    def print_progress(self, curFile, nof_file, chunk, nof_chunks):
        length = 40
        done = int((curFile + 1) / nof_file * length)
        bar = 'X' * done + '-' * (length - done)
        print('\r%s file %d of %d, chunk %d of %d' % (bar, curFile + 1, nof_file, chunk + 1, nof_chunks), end='\r')
        if curFile + 1 == nof_file and chunk + 1 == nof_chunks:
            print()
