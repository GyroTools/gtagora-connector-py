from gtagora.exception import AgoraException
from gtagora.models.base import LinkToFolderMixin, BaseModel, TagMixin, RatingMixin
from gtagora.models.breadcrumb import Breadcrumb
from gtagora.models.dataset import Dataset
from gtagora.models.datafile import Datafile
from gtagora.models.exam import Exam
from gtagora.models.folder_item import FolderItem
from gtagora.models.import_package import import_data
from gtagora.models.series import Series
from gtagora.utils import remove_illegal_chars

from pathlib import Path
from typing import List
from functools import partial


class Folder(LinkToFolderMixin, TagMixin, RatingMixin, BaseModel):
    BASE_URL = '/api/v1/folder/'
    BASE_URL_V2 = '/api/v2/folder/'

    V2_DEFAULT = True

    def get_items(self):
        items = []

        # we get the folder items with the v1 url because then the datafiles are included in the datasets
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

    def is_subfolder_of(self, folder):
        if isinstance(folder, Folder):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise AgoraException('The folder argument must either be a Folder class or a folder ID')

        breadcrumb = self.get_breadcrumb()
        for b in breadcrumb:
            if b.object_id == folder_id:
                return True

        return False

    def get_folder(self, path):
        if isinstance(path, str):
            path = Path(path)

        breadcrumb = None
        cur_breadcrumb_index = None
        cur_folder = self
        for part in path.parts:
            if part:
                if part == '..':
                    if not breadcrumb:
                        breadcrumb = cur_folder.get_breadcrumb()
                        cur_breadcrumb_index = len(breadcrumb)-1
                    cur_breadcrumb_index -= 1
                    cur_breadcrumb_index = max(cur_breadcrumb_index, 0)
                elif part == '.':
                    continue
                else:
                    if cur_breadcrumb_index:
                        cur_folder = self._get_object(breadcrumb[cur_breadcrumb_index].object_id)
                        breadcrumb = None
                        cur_breadcrumb_index = None
                    cur_folder = cur_folder._get_by_name(part, Folder)
                    if not cur_folder:
                        return cur_folder

        if cur_breadcrumb_index:
            cur_folder = self._get_object(breadcrumb[cur_breadcrumb_index].object_id)
        return cur_folder

    def get_folders(self, recursive=False):
        folders = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Folder):
                folders.append(item.object)
                if recursive and hasattr(item, 'object'):
                    folders = folders + item.object.get_folders(recursive)

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

    def get_exam(self, name):
        return self._get_by_name(name, Exam)

    def get_series(self, recursive=False):
        series = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Series):
                series.append(item.object)
            if recursive and isinstance(item, Folder):
                series = series + item.get_series(recursive)

        return series

    def get_serie(self, name):
        return self._get_by_name(name, Series)

    def get_datasets(self, recursive=False):
        datasets = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Dataset):
                datasets.append(item.object)
            if recursive and isinstance(item, Folder):
                datasets.extend(item.get_datasets(recursive))

        return datasets

    def get_dataset(self, name):
        return self._get_by_name(name, Dataset)

    def get_breadcrumb(self):
        url = f'{self.BASE_URL}{self.id}/breadcrumb/?limit=10000000000'
        return self._get_object_list(url, None, Breadcrumb)

    def path(self):
        breadcrumb = self.get_breadcrumb()
        first = True
        p = ''
        for b in breadcrumb:
            if not first:
                p += '/'
            p+= b.name
            first = False
        return p

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

    def upload(self, paths: List[Path], wait=False, verbose=False, relations: dict =None):
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.as_posix())
        return import_data(self.http_client, paths=paths, target_folder_id=self.id, wait=wait, verbose=verbose, relations=relations)

    def create_folder(self, name):
        url = f'{self.BASE_URL}{self.id}/new/'
        post_data = {"name": name}
        response = self.http_client.post(url, json=post_data)
        if response.status_code == 201:
            data = response.json()
            if 'content_object' in data:
                return Folder.from_response(data['content_object'], http_client=self.http_client)

        raise AgoraException(f'Could not create the folder {name}')

    def get_or_create(self, path):
        if isinstance(path, str):
            path = Path(path)

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

    def delete_item(self, ids):
        for id in ids:
            url = f'/api/v1/folderitem/delete_ids/'
            response = self.http_client.post(url, json={"ids": ids}, timeout=60)

    def parent(self):
        breadcrumb = self.get_breadcrumb()
        if len(breadcrumb) > 1:
            id = breadcrumb[-2].object_id
            return self._get_object(id)
        else:
            return None

    def _get_by_name(self, name, instance):
        items = self.get_items()
        for item in items:
            if isinstance(item.object, instance) and item.object.name == name:
                return item.object

        return None

    def __str__(self):
        return f"Folder: {self.name}"
