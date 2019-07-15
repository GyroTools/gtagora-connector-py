from pathlib import Path

import pytest

from gtagora.http.connection import BasicConnection
from tests.helper import FakeClient


@pytest.fixture()
def http_client():
    connection = BasicConnection('http://localhost', 'test', 'test')
    http_client = FakeClient(connection)

    return http_client


@pytest.fixture()
def tempdir_with_dummy_files(tmpdir):
    temp_path = Path(tmpdir)
    for idx in range(0, 5):
        for subdir_idx in range(0, 5):
            p = temp_path / f'{subdir_idx}'
            p.mkdir(parents=True, exist_ok=True)
            with open(p / f'test_{idx}.xyz', 'wb') as f:
                f.write(b'01234567890123456789')

    return Path(tmpdir)


@pytest.fixture()
def zip_upload_files_test_data(tmpdir):

    class TestData:
        def __init__(self):

            self.temp_path = Path(tmpdir)
            self.upload_path = self.temp_path / 'uploads'
            self.upload_path.mkdir(parents=True, exist_ok=True)

            self.input_files = []
            self.target_files = []

            for idx in range(0, 5):
                for subdir_idx in range(0, 5):
                    p = self.temp_path / f'{subdir_idx}'
                    p.mkdir(parents=True, exist_ok=True)
                    file = p / f'test_{idx}.xyz'
                    with open(file, 'wb') as f:
                        f.write(b'0123456789' * 1024 * (idx + 1) * (subdir_idx + 1))
                        self.input_files.append(file)
                        self.target_files.append(file.relative_to(self.temp_path).as_posix())

    return TestData()
