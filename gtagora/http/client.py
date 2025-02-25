import hashlib
import json
import math
import os
import time
import uuid
from dataclasses import dataclass, make_dataclass
from pathlib import Path
from typing import Union, List

import requests

from gtagora.exception import AgoraException
from gtagora.utils import sha256, UploadFile, UploadState


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

    def upload(self, url, files: List[UploadFile], verify_hash=False, max_retries=5, progress_callback=None):
        response = self.get('/api/v1/version/')
        if response.status_code == 200:
            data = response.json()
        else:
            raise AgoraException("cannot connect to the Agora server")

        for index, cur_file in enumerate(files):
            if not cur_file.file.exists() or not cur_file.file.is_file():
                raise AgoraException('Could not open file ' + str(cur_file.file))

            filesize = cur_file.file.stat().st_size
            nof_chunks = math.ceil(filesize / self.UPLOAD_CHUCK_SIZE)
            files[index].nr_chunks = nof_chunks

            filename = cur_file.file.name
            target_filename = cur_file.target

            if files[index].identifier is not None:
                uid = files[index].identifier
            else:
                uid = str(uuid.uuid4())
                files[index].identifier = uid

            start_chunk = files[index].chunks_completed if files[index].chunks_completed is not None else 0

            with open(cur_file.file, mode='rb') as file:
                if start_chunk > 0:
                    file.seek(start_chunk * self.UPLOAD_CHUCK_SIZE, os.SEEK_SET)
                # chunk number starts from 1
                for chunk in range(start_chunk+1, nof_chunks+1):
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            if progress_callback:
                                progress_callback(files[index])
                            data = file.read(self.UPLOAD_CHUCK_SIZE)
                            files_to_upload = {'file': (filename, data)}
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
                            if verify_hash:
                                sha256 = hashlib.sha256()
                                sha256.update(data)
                                data_hash = sha256.hexdigest()
                                form['flowFileContentHash'] = data_hash
                            response = self.post(url, files=files_to_upload, data=form, timeout=self.UPLOAD_TIMEOUT)
                            if response.status_code != 200:
                                raise AgoraException(
                                    f"Failed to upload chunk {chunk} of file {cur_file}. Status code: {response.status_code}")
                            break
                        except requests.exceptions.RequestException as e:
                            # Connection error, retry after waiting for a few seconds
                            retry_count += 1
                            delay = 2 ** retry_count
                            time.sleep(delay)
                    else:
                        raise AgoraException(f"Failed to upload chunk {chunk} after {max_retries} retries.")

                    files[index].chunks_completed = chunk
                    files[index].size_uploaded += len(data)

                    if progress_callback:
                        progress_callback(files[index])

        return True

    def get_total_size(self, files: List[UploadFile]):
        total_size = 0
        for file in files:
            total_size += file.file.stat().st_size
        return total_size

