from gtagora.models.base import BaseModel
from gtagora.utils import sha1
from gtagora.exception import DownloadError

import logging
from pathlib import Path

logger = logging.getLogger("gtAgora")


class Datafile(BaseModel):
    BASE_URL = '/api/v1/datafile/'

    def download(self, path: Path):
        # if not filename:
        #     head, tail = os.path.split(self.rel_filename)
        #     filename = tail

        # if os.path.isdir(filename):
        #     filename = os.path.join(filename, self.rel_filename)

        final_path = path / self.original_filename
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.check_for_existing_file(final_path):
            url = f'{self.BASE_URL}{self.id}/download/'
            self.http_client.download(url, final_path.as_posix())

        # downloaded_file = deepcopy(self)
        # downloaded_file.download_path = filename
        return final_path

    def check_for_existing_file(self, desired_path: Path):
        if desired_path.exists():
            if desired_path.is_file():
                if self.size == desired_path.stat().st_size and sha1(desired_path) == self.sha1:
                    return True
            else:
                raise DownloadError(f"File already exists but it's not a file. {desired_path}")
        return False

    def __str__(self):
        return f'{self.original_filename} {self.size}'
