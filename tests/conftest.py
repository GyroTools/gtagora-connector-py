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
