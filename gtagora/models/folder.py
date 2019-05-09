from gtagora.exception import AgoraException
from gtagora.models.base import LinkToFolderMixin, ShareMixin, BaseModel
from gtagora.models.dataset import Dataset
from gtagora.models.exam import Exam
from gtagora.models.folder_item import FolderItem
from gtagora.models.series import Series
from gtagora.utils import _import_data


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
        Datasets = []
        items = self.get_items()
        for item in items:
            if isinstance(item.object, Dataset):
                Datasets.append(item.object)
            if recursive and isinstance(item, Folder):
                Datasets = Datasets + item.get_series(recursive)

        return Datasets

    def download(self, target_path=None, recursive=None):
        downloaded_files = []
        # Get all Exams in the current folder and download them
        exams = self.get_exams()
        for exam in exams:
            downloaded_files = downloaded_files + exam.Download(target_path)

        # Get all Series in the current folder and download them
        series = self.get_series()
        for s in series:
            downloaded_files = downloaded_files + s.Download(target_path)

        # Get all Datasets in the current folder and download them
        datasets = self.get_datasets()
        for dataset in datasets:
            downloaded_files = downloaded_files + dataset.download(target_path)

        # Download all subfolders as well when the recursive option is true
        if recursive:
            Subfolder = self.get_folders()
            for curSubfolder in Subfolder:
                downloaded_files = downloaded_files + curSubfolder.Download(target_path, recursive)

        return downloaded_files

    def download_exams(self, aTargetPath=None, recursive=None):
        vDownloadedFiles = []
        # Get all Exams in the current folder and download them
        Exams = self.get_exams()
        for curExam in Exams:
            vDownloadedFiles = vDownloadedFiles + curExam.Download(aTargetPath)

        # Download all exams in subfolders as well when the recursive option is true
        if recursive:
            Subfolder = self.get_folders()
            for curSubfolder in Subfolder:
                vDownloadedFiles = vDownloadedFiles + curSubfolder.DownloadExams(aTargetPath, recursive)

        return vDownloadedFiles

    def download_series(self, aTargetPath=None, recursive=None):
        vDownloadedFiles = []
        # Get all Series in the current folder and download them
        Series = self.get_series()
        for curSeries in Series:
            vDownloadedFiles = vDownloadedFiles + curSeries.Download(aTargetPath)

        # Download all series in subfolders as well when the recursive option is true
        if recursive:
            Subfolder = self.get_folders()
            for curSubfolder in Subfolder:
                vDownloadedFiles = vDownloadedFiles + curSubfolder.DownloadSeries(aTargetPath, recursive)

        return vDownloadedFiles

    def download_datasets(self, aTargetPath=None, recursive=None):
        vDownloadedFiles = []
        # Get all Datasets in the current folder and download them
        Datasets = self.get_datasets()
        for curDatasets in Datasets:
            vDownloadedFiles = vDownloadedFiles + curDatasets.Download(aTargetPath)

        # Download all datasets in subfolders as well when the recursive option is true
        if recursive:
            Subfolder = self.get_folders()
            for curSubfolder in Subfolder:
                vDownloadedFiles = vDownloadedFiles + curSubfolder.DownloadSeries(aTargetPath, recursive)

        return vDownloadedFiles

    def upload(self, files, target_files=None, wait=True, progress=False):
        return _import_data(self.http_client, files, self, target_files, None, wait, progress)

    def upload_dataset(self, input_files, type, target_files=None):
        # This function creates a dataset of a given type all files given as input will be added to one dataset.
        # Please note: At the moment there is no consistency check. We could create datasets with improper
        # files (e.g. a PAR/REC dataset without PAR/REC files)
        return self.http_client.upload_dataset(input_files, target_files, self.http_client, FolderID=self.id, type=type)

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

        next_folder = self
        for part in path.split('/'):
            next_folder_exists = False
            for folder in next_folder.get_folders():
                if folder.name == part:
                    next_folder = folder
                    next_folder_exists = True
                    break;
            if not next_folder_exists:
                next_folder = next_folder.create_folder(part)

        return next_folder