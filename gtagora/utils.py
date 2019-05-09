import os
import zipfile
from pathlib import Path

def to_path_array(files):
    try:
        if isinstance(files, str):
            return [Path(files)]

        if isinstance(files, Path):
            return [files]

        iter(files)

        if len(files) > 0:
            if isinstance(files[0], Path):
                return files

            if isinstance(files[0], str):
                return [Path(f) for f in files]

        return []
    except TypeError:
        raise TypeError("Excepting str, pathlib.Path, [str] or [pathlib.Path]")


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


def _import_data(http_client, files, target_folder=None, target_files=None, json_import_file=None, wait=True,
                progress=False):

    from gtagora.models.import_package import ImportPackage
    """
    Import a directory or a list of files with optional target file names.

    The target folder is optional. If
    target_folder is None and data is uploaded that can't be trated as an exam or series a new folder in the
    root will be created.

    :param files: One directroy or multiple files as string or Path
    :param target_folder: The target folder
    :param wait: Wait until the upload and import process ha sbeen finished
    :returns: The import package. Can be used to watch the upload
    """
    files = to_path_array(files)

    if not files:
        return None

    for f in files:
        if not f.exists():
            raise FileNotFoundError(f.as_posix())

    import_package = ImportPackage(http_client=http_client).create()

    if len(files) == 1 and files[0].is_dir():
        import_package.upload_directory(files[0],
                                        target_folder_id=target_folder.id,
                                        wait=wait,
                                        progress=progress)
    else:
        if not all([f.is_file() for f in files]):
            raise Exception('''Can not upload a list of files and directories. Only one directroy or multiple 
files are supported''')

        import_package.upload(files,
                              target_folder_id=target_folder.id,
                              target_files=target_files,
                              json_import_file=json_import_file,
                              wait=wait,
                              progress=progress)
    return import_package


class ZipUploadFiles:

    MAX_FILE_LIMIT = 100*1024*1024

    def __init__(self, input_files, target_files):
        self.input_files = input_files
        self.target_files = target_files
        self._zip_is_required = False

    def create_zip(self, path):
        files_to_zip = self._create_file_list()

        if self._zip_is_required is False:
            return self.input_files, self.target_files

        index = 0
        input_files = []
        target_files = []

        while index < len(files_to_zip):

            zip_filename = f'upload_{index}.agora_upload'
            zip_path = Path(path, zip_filename)
            input_files.append(zip_path.as_posix())
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
                    if compressed_size > 2*1024*1024*1024:
                        break

        return input_files, target_files

    def _create_file_list(self):

        def create_entry(file, target_file):
            size = os.path.getsize(file)
            do_zip = size < self.MAX_FILE_LIMIT

            if do_zip:
                self._zip_is_required = True

            return file, target_file, do_zip

        file_list = [create_entry(file, target_file) for file, target_file in zip(self.input_files, self.target_files)]
        return file_list


