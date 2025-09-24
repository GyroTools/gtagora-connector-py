import datetime
import math
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import List

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.utils import ZipUploadFiles, sha1, UploadFile, UploadState


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
        full_url = self.http_client.connection.url + url
        raise AgoraException(f"Can't create an Import object: url={full_url} status_code={response.status_code}")

    def upload(self, input_files: List[Path], target_folder_id: int = None, exam_id=None, series_id= None,
               json_import_file=None, wait=True, timeout: int = None, verbose=False, relations: dict = None,
               progress_file: Path = None):

        if progress_file is not None and not isinstance(progress_file, Path):
            raise AgoraException(f'progress must be a Path object')

        if progress_file and not progress_file.exists():
            progress_file.parent.mkdir(parents=True, exist_ok=True)

        state = self.create_state(input_files, target_folder_id=target_folder_id, exam_id=exam_id, series_id=series_id,
                                  json_import_file=json_import_file, wait=wait, timeout=timeout, verbose=verbose,
                                  relations=relations)

        state.save(progress_file)
        return self.upload_from_state(state, progress_file=progress_file)

    def create_state(self, input_files: List[Path], target_folder_id: int = None, exam_id=None, series_id=None,
                     json_import_file=None, wait=True, timeout: int = None, verbose=False, relations: dict = None):
        state = self._create_upload_state(input_files, relations=relations)
        state.target_folder_id = target_folder_id
        state.exam_id = exam_id
        state.series_id = series_id
        state.json_import_file = json_import_file
        state.wait = wait
        state.timeout = timeout
        state.verbose = verbose
        return state

    def upload_from_state(self, state: UploadState, progress_file: Path = None):
        def progress_callback(file: UploadFile):
            if state and state.files:
                # update state
                index = next((i for i, item in enumerate(state.files) if item.file == file.file), None)
                if index:
                    state.files[index] = file

                if progress_file is not None:
                    state.save(progress_file)

                if state.verbose:
                    total_size = sum([f.size for f in state.files])
                    size_uploaded = sum([f.size for f in state.files if f.uploaded])
                    if not file.uploaded:
                        size_uploaded += file.size_uploaded
                    elif not index:
                        # the file is a zip file and it is uploaded. However the files in the state have nt yet received
                        # the uploaded flag.
                        return

                    files_uploaded = len([f for f in state.files if f.uploaded])
                    appendix = f'({self.pretty_print_progress(size_uploaded, total_size)}, file {files_uploaded} of {len(state.files)})'
                    self.print_progress(progress=size_uploaded/total_size, appendix=appendix)

        base_url = '/api/v1/import/' + str(self.id) + '/'
        url = base_url + 'upload/'
        zip_packages = self._create_zip_packages(state)

        if state.verbose:
            print(f'import package: {self.id}')
            print("uploading...")

        if len(zip_packages) > 0:
            for package in zip_packages:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_upload = ZipUploadFiles(package)
                    files = zip_upload.create_zip(Path(temp_dir), single_file=True, zip_filename=f'upload_{str(uuid.uuid4())}.agora_upload')
                    response = self.http_client.upload(url, files, progress_callback=progress_callback)
                    self._set_uploaded(state, package)
                    state.save(progress_file)

        # create a list of the files which are uploaded unzipped. The entries of the new list are a reference to the
        # original list so that the state is changed as well
        files_to_upload_indices = [i for i, f in enumerate(state.files) if not f.zip and not f.uploaded]
        files_to_upload = [state.files[i] for i in files_to_upload_indices]
        if files_to_upload and len(files_to_upload) > 0:
            response = self.http_client.upload(url, files_to_upload, progress_callback=progress_callback)

        if state.verbose:
            total_size = sum([f.size for f in state.files])
            appendix = f'({self.pretty_print_progress(total_size, total_size)}, file {len(state.files)} of {len(state.files)})'
            self.print_progress(progress=1, appendix=appendix)

        if self.complete(state.json_import_file, target_folder_id=state.target_folder_id, exam_id=state.exam_id,
                         series_id=state.series_id, relations=state.relations):
            if state.wait:
                if state.verbose:
                    print("\nimporting data...")
                start_time = datetime.datetime.now()
                while (datetime.datetime.now() - start_time).seconds < state.timeout if state.timeout else True:
                    data = self.progress()
                    if data['state'] == 5 or data['state'] == 4:
                        if state.verbose:
                            count = data.get('tasks', {}).get('count', 0)
                            finished = data.get('tasks', {}).get('finished', 0)
                            progress = finished / count if count > 0 else 0
                            self.print_progress(progress=progress)
                        if data['state'] == 5 and data['progress'] == 100:
                            self._update_import_state(state)
                            state.save(progress_file)
                            if state.verbose:
                                self.print_final_message(state)
                            return state
                    elif data['state'] == -1:
                        print("Import failed")
                        return state
                    time.sleep(5)

                raise AgoraException(f'connection timed out while waiting for the import to finish')

    def complete(self, json_import_file=None, target_folder_id=None, exam_id=None, series_id=None, relations: dict = None):
        url = self.BASE_URL + str(self.id) + '/complete/'
        post_data = {}
        if json_import_file:
            post_data.update({'import_file': json_import_file})
        if target_folder_id:
            post_data.update({'folder': target_folder_id})
        if exam_id:
            post_data.update({'exam': exam_id})
        if series_id:
            post_data.update({'series': series_id})
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
        if response.status_code == 200:
            data = response.json()
            datafiles = []

            if not data:
                return

            if data and not 'datafiles' in data:
                for file in state.files:
                    file.imported = True
                return

            for datafile in data['datafiles']:
                indices = [i for i, f in enumerate(state.files) if Path(f.target) == Path(datafile['path']) and f.imported is False]
                if indices and len(indices) > 0:
                    for index in indices:
                        local_sha1 = sha1(Path(state.files[index].file))
                        if local_sha1 == datafile['sha1']:
                            state.files[index].imported = True
                            break

        return

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
                 size=Path(file).stat().st_size, nr_chunks=None,
                 chunks_completed=None, identifier=None, uploaded=False, imported=False)
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

    @staticmethod
    def print_progress(progress: float = 0.0, appendix=''):
        length = 40
        done = math.ceil(progress * length)
        bar = 'o' * done + '-' * (length - done)
        print('\r%s %d%% %s' % (bar, math.ceil(progress * 100), appendix), end='', flush=True)

    @staticmethod
    def pretty_print_progress(size1, size2):
        """Take two sizes in bytes and return them in a human-readable format."""
        units = ['bytes', 'KB', 'MB', 'GB', 'TB']
        for unit in units:
            if size2 < 1024.0:
                return f"{size1:.1f}/{size2:.1f}{unit}"
            size1 /= 1024.0
            size2 /= 1024.0
        return f"{size1:.1f}/{size2:.1f} PB"

    def print_final_message(self, state):
        if state.verbose:
            nr_datafiles_imported = len([f for f in state.files if f.imported])
            success = all([f.imported for f in state.files])
            print("\nImport complete:")
            print(f'  Files Uploaded: {len(state.files)}, Files Imported: {nr_datafiles_imported}')
            if success:
                print(f"\nAll files sucessfully imported.")
            else:
                print(f"\nSome files were not imported:")
                not_imported = [f for f in state.files if not f.imported]
                for f in not_imported:
                    print(f"  {f.file}")
        return state


def import_data(http_client, paths: List[Path], target_folder_id: int = None, exam_id=None, series_id= None,
                json_import_file: Path = None, wait=True, verbose=False, relations: dict =None,
                progress_file: Path = None):
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

    if json_import_file:
        if not json_import_file.exists():
            raise FileNotFoundError(f"json_import_file {json_import_file} not found")

    # add json_import_file to the input_files if it is not already there
    extended_paths = [p for p in paths]
    if json_import_file and json_import_file not in paths:
        extended_paths.append(json_import_file)

    state = import_package.upload(extended_paths,
                          target_folder_id=target_folder_id,
                          exam_id=exam_id,
                          series_id=series_id,
                          json_import_file=json_import_file.name if json_import_file else None,
                          wait=wait,
                          verbose=verbose,
                          relations=relations,
                          progress_file=progress_file)
    return state
