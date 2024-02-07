from pathlib import Path
from typing import List

from gtagora.exception import AgoraException
from gtagora.models.import_package import ImportPackage
from gtagora.utils import UploadState


class UploadSession:
    def __init__(self, http_client, paths: List[Path] = None, target_folder_id: int = None, json_import_file: Path = None,
                verbose=False, relations: dict = None, progress_file: Path = None):

        self.progress_file = progress_file
        if paths is not None and len(paths) > 0:
            import_package = ImportPackage(http_client=http_client).create()
            if json_import_file:
                if not json_import_file.exists():
                    raise FileNotFoundError(f"json_import_file {json_import_file} not found")

            if progress_file is not None and not isinstance(progress_file, Path):
                raise AgoraException(f'progress must be a Path object')

            if progress_file and not progress_file.exists():
                progress_file.parent.mkdir(parents=True, exist_ok=True)

            state = import_package.create_state(paths, target_folder_id=target_folder_id,
                                                json_import_file=json_import_file, wait=True, verbose=verbose,
                                                relations=relations)

            self.state = state
            self.import_package = import_package
        elif progress_file is not None and progress_file.exists():
            state = UploadState.from_file(progress_file)
            import_package = ImportPackage.get(state.import_package, http_client=http_client)
            self.state = state
            self.import_package = import_package
        else:
            raise AgoraException('Either a path list or an existing progress_file must be given as argument')

    def start(self):
        return self.import_package.upload_from_state(self.state, self.progress_file)