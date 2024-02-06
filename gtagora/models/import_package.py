import datetime
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.utils import ZipUploadFiles, sha1, UploadFile, EnhancedJSONEncoder, UploadState


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
               timeout: int = None, verbose=False, relations: dict = None, progress: Path = None):

        if not isinstance(progress, Path):
            raise AgoraException(f'progress must be a Path object')

        if progress and not progress.exists():
            progress.parent.mkdir(parents=True, exist_ok=True)

        state = self._create_upload_state(input_files, relations=relations)
        state.target_folder_id = target_folder_id
        state.json_import_file = json_import_file
        state.wait = wait
        state.timeout = timeout
        state.verbose = verbose

        state.save(progress)
        return self._upload(state, progress=progress)

    def _upload(self, state: UploadState, progress: Path = None):
        base_url = '/api/v1/import/' + str(self.id) + '/'
        url = base_url + 'upload/'

        zip_packages = self._create_zip_packages(state)

        if len(zip_packages) > 0:
            if state.verbose:
                print("uploading small files as zip..")
            for package in zip_packages:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_upload = ZipUploadFiles(package)
                    files = zip_upload.create_zip(Path(temp_dir), single_file=True)
                    response = self.http_client.upload(url, files, verbose=state.verbose)
                    self._set_uploaded(state, package)
                    state.save(progress)

        # create a list of the files which are uploaded unzipped. The entries of the new list are a reference to the
        # original list so that the state is changed as well
        if state.verbose:
            print("uploading large files..")
        files_to_upload_indices = [i for i, f in enumerate(state.files) if not f.zip and not f.uploaded]
        files_to_upload = [state.files[i] for i in files_to_upload_indices]
        if files_to_upload and len(files_to_upload) > 0:
            response = self.http_client.upload(url, files_to_upload, verbose=state.verbose, progress=progress)

        if self.complete(state.json_import_file, target_folder_id=state.target_folder_id, relations=state.relations):
            if state.wait:
                if state.verbose:
                    print("importing data...")
                start_time = datetime.datetime.now()
                while (datetime.datetime.now() - start_time).seconds < state.timeout if state.timeout else True:
                    data = self.progress()
                    if data['state'] == 5 or data['state'] == -1:
                        nr_datafiles_imported = self._update_import_state(state)
                        state.save(progress)
                        if state.verbose:
                            print("Import complete:")
                            print(f'  Files Uploaded: {len(state.files)}, Files Imported: {nr_datafiles_imported}')
                        return state
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

    def _group_files_by_size(self, files, max_group_size):
        file_groups = []
        current_group = []
        current_group_size = 0

        for file in files:
            file_path = file.file
            file_size = os.path.getsize(file_path)

            if current_group_size + file_size > max_group_size:
                file_groups.append(current_group)
                current_group = []
                current_group_size = 0

            current_group.append(file)
            current_group_size += file_size

        if current_group:
            file_groups.append(current_group)

        return file_groups

    def _update_import_state(self, state):
        url = self.BASE_URL + str(self.id) + '/result/'

        response = self.http_client.get(url)
        nr_datafiles = 0
        if response.status_code == 200:
            data = response.json()
            datafiles = []
            for entry in data:
                datafiles.extend(entry.get('datafiles', []))
            for datafile in datafiles:
                indices = [i for i, f in enumerate(state.files) if Path(f.target).name == datafile['name']]
                if indices and len(indices) > 0:
                    for index in indices:
                        local_sha1 = sha1(Path(state.files[index].file))
                        if local_sha1 == datafile['sha1']:
                            state.files[index].imported = True
                            nr_datafiles += 1
                            break

        return nr_datafiles

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
        if not relations:
            return None

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

    def _create_upload_state(self, input_files, relations: dict = None):
        input_files, target_files = self._prepare_paths_to_upload(input_files)
        relations = self._prepare_relations(relations, input_files, target_files)
        files = [UploadFile(id=index, file=Path(file), target=str(target), zip=len(input_files) > 5 and self._do_zip_file(file),
                  nr_chunks=None, chunks_completed=None, identifier=None, uploaded=False, imported=False)
                 for index, (file, target) in enumerate(zip(input_files, target_files))]
        state = UploadState(import_package=self.id, files=files, relations=relations)
        return state

    def _do_zip_file(self, file):
        filesize = os.path.getsize(file)
        return filesize < ZipUploadFiles.MAX_FILE_LIMIT

    def _create_zip_packages(self, state):
        files_to_zip = [f for f in state.files if f.zip and not f.uploaded]
        compression_rate = 3
        max_group_size = self.http_client.UPLOAD_CHUCK_SIZE * compression_rate
        packages = self._group_files_by_size(files_to_zip, max_group_size)
        return packages

    def _set_uploaded(self, state, files):
        for file in files:
            id = file.id
            index = next((index for (index, d) in enumerate(state.files) if d.id == id), None)
            state.files[index].uploaded = True
        return state


def import_data(http_client, paths: List[Path], target_folder_id: int = None, json_import_file: Path = None, wait=True,
                verbose=False, relations: dict =None, progress: Path = None):
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
    import_package = ImportPackage(http_client=http_client).create()
    print("ImportPackage ID={}".format(import_package.id))

    if json_import_file:
        if not json_import_file.exists():
            raise FileNotFoundError(f"json_import_file {json_import_file} not found")

    state = import_package.upload(paths,
                          target_folder_id=target_folder_id,
                          json_import_file=json_import_file.name if json_import_file else None,
                          wait=wait,
                          verbose=verbose,
                          relations=relations,
                          progress=progress)
    return state


def resume_import(http_client, progress: Path):
    if not progress.exists():
        raise FileNotFoundError(f"progress file {progress} does not exist")

    state = UploadState.from_file(progress)
    import_package = ImportPackage.get(state.import_package, http_client=http_client)
    import_package._upload(state, progress=progress)
    return state