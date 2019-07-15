from gtagora.exception import AgoraException
from gtagora.models.base import LinkToFolderMixin, ShareMixin, BaseModel
from gtagora.models.dataset import Dataset
from gtagora.models.datafile import Datafile
from gtagora.models.exam import Exam
from gtagora.models.folder_item import FolderItem
from gtagora.models.series import Series
from gtagora.utils import remove_illegal_chars

from pathlib import Path
from typing import List
from functools import partial


class Folder(LinkToFolderMixin, ShareMixin, BaseModel):
    BASE_URL = '/api/v1/folder/'

    def get_items(self):
        items = []

        url = self.BASE_URL + str(self.id) + '/items/?limit=10000000000'
        response = self.http_client.get(url)

        for item in response.json():
            if 'content_object' in item and 'content_type' in item:
                items.append(FolderItem.from_response(item, http_client=self.http_client))

        return items

    def is_folder(self, name):
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Folder) and item.object.name == name:
                return True

        return False

    def get_folder(self, name):
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Folder) and item.object.name == name:
                return item.object

        return None

    def get_folders(self, recursive=False):
        folders = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Folder):
                folders.append(item.object)
                if recursive:
                    folders = folders + item.get_folders(recursive)

        return folders

    def get_exams(self, recursive=False):
        exams = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Exam):
                exams.append(item.object)
            if recursive and isinstance(item, Folder):
                exams = exams + item.get_exams(recursive)

        return exams

    def get_series(self, recursive=False):
        series = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Series):
                series.append(item.object)
            if recursive and isinstance(item, Folder):
                series = series + item.get_series(recursive)

        return series

    def get_datasets(self, recursive=False):
        datasets = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Dataset):
                datasets.append(item.object)
            if recursive and isinstance(item, Folder):
                datasets.extend(item.get_series(recursive))

        return datasets

    def download(self, target_path: Path, recursive=False) -> List[Datafile]:

        # Get all Exams in the current folder and download them
        downloaded_files = self.download_exams(target_path, recursive=recursive)
        downloaded_files.extend(self.download_series(target_path, recursive=recursive))
        downloaded_files.extend(self.download_datasets(target_path, recursive=recursive))

        return downloaded_files

    def download_exams(self, target_path: Path, recursive=False):
        exams = self.get_exams()
        return self._download_objects(exams, target_path, Folder.download_exams, recursive)

    def download_series(self, target_path: Path, recursive=False):
        exams = self.get_series()
        return self._download_objects(exams, target_path, Folder.download_series, recursive)

    def download_datasets(self, target_path: Path, recursive=False):
        exams = self.get_datasets()
        return self._download_objects(exams, target_path, Folder.download_datasets, recursive)

    def _download_objects(self, objects, target_path: Path, download_fct, recursive=False):
        downloaded_files = [obj.download(target_path) for obj in objects]

        # Download all exams in subfolders as well when the recursive option is true
        if recursive:
            for folder in self.get_folders():
                downloaded_files.extend(partial(download_fct, folder)(
                    target_path / remove_illegal_chars(folder.name), recursive))

        return downloaded_files

    def upload(self, files, target_files=None, wait=True, progress=False):
        return _import_data(self.http_client, files, self, target_files, None, wait, progress)

    def create_folder(self, name):
        url = f'{self.BASE_URL}{self.id}/new/'
        post_data = {"name": name}
        response = self.http_client.post(url, json=post_data)
        if response.status_code == 201:
            data = response.json()
            if 'content_object' in data:
                return Folder.from_response(data['content_object'], http_client=self.http_client)

        raise AgoraException(f'Could not create the folder {name}')

    def get_or_create(self, path: Path):

        next_folder = self
        for part in path.parts:
            next_folder_exists = False
            for folder in next_folder.get_folders():
                if folder.name == part:
                    next_folder = folder
                    next_folder_exists = True
                    break
            if not next_folder_exists:
                next_folder = next_folder.create_folder(part)

        return next_folder
