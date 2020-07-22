import datetime
import os
import time
import tempfile
from pathlib import Path
from typing import List

from gtagora.models.base import BaseModel
from gtagora.exception import AgoraException
from gtagora.utils import ZipUploadFiles


class ImportPackage(BaseModel):
    mTaskInfoTimeout = 120
    BASE_URL = '/api/v1/import/'

    def __init__(self, http_client=None):
        super().__init__(http_client=http_client)
        self.last_progress = None
        self.zip_upload = False

    def create(self):
        url = self.BASE_URL
        response = self.http_client.post(url, json={}, timeout=60)
        if response.status_code == 201:
            data = response.json()
            if 'id' in data:
                self._set_values(data)
                return self
        raise AgoraException("Can't create an Import object")

    def upload(self, input_files: List[Path], target_folder_id: int = None, json_import_file=None, wait=True,
               timeout: int = None, progress=False, relations: dict = None):

        base_url = '/api/v1/import/' + str(self.id) + '/'
        url = base_url + 'upload/'

        input_files, target_files = self._prepare_paths_to_upload(input_files)
        relations = self._prepare_relations(relations, input_files, target_files)

        if self._check_zip_option(input_files):
            print("Prepare optimized upload")
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_upload = ZipUploadFiles(input_files, target_files)
                input_files, target_files = zip_upload.create_zip(Path(temp_dir))
                response = self.http_client.upload(url, input_files, target_files, progress=progress)
        else:
            self.zip_upload = False
            response = self.http_client.upload(url, input_files, target_files, progress=progress)

        if self.complete(json_import_file, target_folder_id=target_folder_id, relations=relations):
            if wait:
                start_time = datetime.datetime.now()
                while (datetime.datetime.now() - start_time).seconds < timeout if timeout else True:
                    data = self.progress()
                    if data['state'] == 5 or data['state'] == -1:
                        return data
                    time.sleep(5)

        raise AgoraException(f'Failed to complete upload {self.id}: {response.status_code}')

    def complete(self, json_import_file=None, target_folder_id=None, relations: dict = None):
        url = self.BASE_URL + str(self.id) + '/complete/'
        post_data = {}
        if json_import_file:
            post_data.update({'import_file': json_import_file})
        if target_folder_id:
            post_data.update({'folder': target_folder_id})
        if relations:
            post_data.update({'relations': relations})

        response = self.http_client.post(url, json=post_data)
        if response.status_code == 204:
            return True
        raise AgoraException(f'fail to get progress from ImportPackage {self.id}: {response.status_code}')

    def progress(self):
        url = self.BASE_URL + str(self.id) + '/progress/'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'state' not in data:
                raise AgoraException(f'Could not get the task info: {data}')
            self.last_progress = data
            return self.last_progress
        raise AgoraException(f'fail to get progress from ImportPackage {self.id}: {response.status_code}')

    def get_objects(self):
        url = self.BASE_URL + str(self.id) + '/get_objects/'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        raise AgoraException(f'fail to get object from ImportPackage {self.id}: {response.status_code}')

    def _prepare_paths_to_upload(self, paths: List[Path], target_folder_id=None, wait=True, progress=False):
        input_files = []
        target_files = []

        for path in paths:
            if path.is_dir():
                for root, dirs, files in os.walk(path):
                    for f in files:
                        absolute_file_path = Path(root, f)
                        input_files.append(absolute_file_path)
                        target_files.append(absolute_file_path.relative_to(path.parent).as_posix())
            elif path.is_file():
                input_files.append(path.absolute())
                target_files.append(path.name)
            else:
                raise TypeError(f"Can't upload other than a file or a directory: {path.as_posix()}")

        return input_files, target_files

    def _prepare_relations(self, relations, input_files, target_files):
        new_relations = dict()
        all_related_files = []
        for relation_target, related_files in relations.items():
            all_related_files.extend(related_files)
        if len(all_related_files) > len(set(all_related_files)):
            raise AgoraException(f'Related files can only occur once')

        for relation_target, related_files in relations.items():
            target_path = self._to_target_path(relation_target, input_files, target_files)
            if not target_path:
                raise AgoraException(f'The relation {relation_target} is not a file which is uploaded')


            new_related_files = []
            for related_file in related_files:
                new_file = self._to_target_path(related_file, input_files, target_files)
                if not new_file:
                    raise AgoraException(f'The related file {related_file} is not a file which is uploaded')
                new_related_files.append(new_file)
            new_relations[target_path] = new_related_files

        return new_relations

    def _check_zip_option(self, input_files):
        return len(input_files) > 5

    def _to_target_path(self, path: str, input_files, target_files):
        try:
            absolute_path = Path(path).absolute()
            if absolute_path in input_files:
                index = input_files.index(absolute_path)
                return target_files[index]
            elif path in target_files:
                return path
            else:
               return None
        except:
            return None


def import_data(http_client, paths: List[Path], target_folder_id: int = None, json_import_file: Path = None, wait=True,
                progress=False, relations: dict =None):
    """
    Import a directory or a list of files with optional target file names.

    The target folder is optional. If
    target_folder is None and data is uploaded that can't be trated as an exam or series a new folder in the
    root will be created.

    :param files: One directory or multiple files as string or Path
    :param target_folder: The target folder
    :param wait: Wait until the upload and import process ha sbeen finished
    :returns: The import package. Can be used to watch the upload
    """
    from gtagora.models.import_package import ImportPackage

    import_package = ImportPackage(http_client=http_client).create()
    print("ImportPackage ID={}".format(import_package.id))

    if json_import_file:
        if not json_import_file.exists():
            raise FileNotFoundError(f"json_import_file {json_import_file} not found")

    import_package.upload(paths,
                          target_folder_id=target_folder_id,
                          json_import_file=json_import_file.name if json_import_file else None,
                          wait=wait,
                          progress=progress,
                          relations=relations)
    return import_package
