import json
import os
import zipfile
import hashlib
from dataclasses import dataclass, is_dataclass, asdict
from itertools import zip_longest
from pathlib import Path
from typing import List, Union
from urllib.parse import urlparse

from gtagora.exception import AgoraException


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)

@dataclass
class UploadFile:
    id: int
    file: Path
    target: str
    zip: bool = False
    size: Union[int, None] = None
    size_uploaded: int = 0
    nr_chunks: Union[int, None] = None
    chunks_completed: Union[int, None] = None
    identifier: Union[str, None] = None
    uploaded: bool = False
    imported: bool = False

    def json(self):
        return json.dumps(self, cls=EnhancedJSONEncoder)


@dataclass
class UploadState:
    import_package: int
    files: List[UploadFile]
    target_folder_id: Union[dict, None] = None
    exam_id: Union[dict, None] = None
    series_id: Union[dict, None] = None
    json_import_file: Union[Path, None] = None
    relations: Union[dict, None] = None
    wait: bool = True
    verbose: bool = False
    timeout: Union[int, None] = None

    def json(self, indent=None):
        return json.dumps(self, cls=EnhancedJSONEncoder, indent=indent)

    def save(self, file: Path, indent=2):
        if file:
            with file.open('w') as f:
                json.dump(self, f, cls=EnhancedJSONEncoder, indent=indent)

    @staticmethod
    def from_file(file: Path):
        if file and file.exists():
            with file.open('r') as f:
                data = json.load(f)
                state = UploadState(**data)
                state.json_import_file = Path(state.json_import_file) if state.json_import_file else None
                files = [UploadFile(**f) for f in data['files']]
                for f in files:
                    f.file = Path(f.file)
                state.files = files
                return state


def get_file_info(path):
    total_size = 0
    nof_files = 0

    if isinstance(path, str):
        path = Path(path)

    if path.is_file():
        return 1, path.stat().st_size

    for dirpath, dirnames, filenames in os.walk(str(path)):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
        nof_files += len(filenames)
    return nof_files, total_size


class ZipUploadFiles:

    MAX_FILE_LIMIT = 100*1024*1024
    MAX_ZIP_FILE_SIZE = 2*1024*1024*1024

    def __init__(self, input_files: List[UploadFile]):
        self.input_files = input_files
        self._zip_is_required = False

    def create_zip(self, path: Path, single_file=False, zip_filename=None):
        files_to_zip = self._create_file_list(single_file=single_file)

        if self._zip_is_required is False:
            return self.input_files

        index = 0
        zip_files = []

        while index < len(files_to_zip):

            zip_filename = zip_filename if zip_filename is not None else f'upload_{index}.agora_upload'
            zip_path = path / zip_filename
            zip_id = len(zip_files)
            zip_files.append(UploadFile(id=zip_id, file=zip_path, target=zip_filename))

            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as z:
                for file, do_zip in files_to_zip[index:]:
                    if do_zip:
                        z.write(file.file, file.target)
                    else:
                        zip_files.append(UploadFile(id=len(zip_files), file=file.file, target=file.target, size=file.file.stat().st_size))
                    index += 1

                    compressed_size = sum([info.compress_size for info in z.infolist()])
                    if not single_file and compressed_size > self.MAX_ZIP_FILE_SIZE:
                        break

            for f in zip_files:
                if f.id == zip_id:
                    f.size = zip_path.stat().st_size

        return zip_files

    def _create_file_list(self, single_file=False):

        def create_entry(file: UploadFile, single_file=False):
            size = file.file.stat().st_size
            do_zip = single_file or size < self.MAX_FILE_LIMIT

            if do_zip:
                self._zip_is_required = True

            return file, do_zip

        file_list = [create_entry(file, single_file=single_file) for file in self.input_files]
        return file_list


def remove_illegal_chars(path: str):
    illegal = [':', '*', '"', '<', '>', '|']

    for i in illegal:
        path = path.replace(i, '')

    return path


def sha1(path: Path):

    sha1 = hashlib.sha1()
    BUF_SIZE = 1024*1024

    with path.open('rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def sha256(path: Path):
    sha256 = hashlib.sha256()
    BUF_SIZE = 1024 * 1024

    with path.open('rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def validate_url(url):
    # check if the url has a scheme. If not then add it
    u = urlparse(url)
    if u.scheme != 'http' and u.scheme != 'https':
        raise AgoraException('the URL must start with http:// or https://')

    if u.path:
        url = u.scheme + '://' + u.netloc

    return url
