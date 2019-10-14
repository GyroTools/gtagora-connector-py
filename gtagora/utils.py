import os
import zipfile
import hashlib
from itertools import zip_longest
from pathlib import Path
from urllib.parse import urlparse


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

    def __init__(self, input_files, target_files):
        self.input_files = input_files
        self.target_files = target_files if target_files else []
        self._zip_is_required = False

    def create_zip(self, path: Path):
        files_to_zip = self._create_file_list()

        if self._zip_is_required is False:
            return self.input_files, self.target_files

        index = 0
        input_files = []
        target_files = []

        while index < len(files_to_zip):

            zip_filename = f'upload_{index}.agora_upload'
            zip_path = path / zip_filename
            input_files.append(zip_path)
            target_files.append(zip_filename)

            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as z:
                for file, target_file, do_zip in files_to_zip[index:]:
                    if do_zip:
                        z.write(file, target_file)
                    else:
                        input_files.append(file)
                        target_files.append(target_file)
                    index += 1

                    compressed_size = sum([info.compress_size for info in z.infolist()])
                    if compressed_size > self.MAX_ZIP_FILE_SIZE:
                        break

        return input_files, target_files

    def _create_file_list(self):

        def create_entry(file, target_file):
            size = os.path.getsize(file)
            do_zip = size < self.MAX_FILE_LIMIT

            if do_zip:
                self._zip_is_required = True

            return file, target_file, do_zip

        file_list = [create_entry(file, target_file)
                     for file, target_file in zip_longest(self.input_files, self.target_files)]
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

def validate_url(url):
    # check if the url has a scheme. If not then add it
    u = urlparse(url)
    if u.scheme != 'http' and u.scheme != 'https':
        url = 'http://' + url
        u = urlparse(url)

    if u.path:
        url = u.scheme + '://' + u.netloc

    return url
