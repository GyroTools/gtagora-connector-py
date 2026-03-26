import zipfile
from pathlib import Path

import pytest

from gtagora.exception import AgoraException
from gtagora.utils import get_file_info, UploadFile, ZipUploadFiles, validate_url


def test_get_file_info(tempdir_with_dummy_files):
    temp_path = tempdir_with_dummy_files

    nof_files, total_size = get_file_info(temp_path)
    assert nof_files == 25
    assert total_size == 500

    nof_files, total_size = get_file_info(temp_path / '0/test_0.xyz')
    assert nof_files == 1
    assert total_size == 20


class TestZipUploadFiles:

    def _make_upload_files(self, input_files, target_files):
        return [UploadFile(id=i, file=f, target=t) for i, (f, t) in enumerate(zip(input_files, target_files))]

    def test_create_zip_1(self, zip_upload_files_test_data):
        test_data = zip_upload_files_test_data
        upload_path = test_data.upload_path
        upload_files = self._make_upload_files(test_data.input_files, test_data.target_files)

        result = ZipUploadFiles(upload_files).create_zip(upload_path)

        assert len(result) == 1
        assert result[0].file == Path(upload_path, 'upload_0.agora_upload')
        assert result[0].target == 'upload_0.agora_upload'

        with zipfile.ZipFile(result[0].file, 'r') as z:
            assert len(z.infolist()) == 25
            assert [info.filename for info in z.infolist()] == test_data.target_files

    def test_create_zip_2(self, zip_upload_files_test_data):
        test_data = zip_upload_files_test_data
        temp_path = test_data.temp_path
        upload_path = test_data.upload_path
        upload_files = self._make_upload_files(test_data.input_files, test_data.target_files)

        ZipUploadFiles.MAX_FILE_LIMIT = 100*1024  # Zip all files smaller than 100 KB

        result = ZipUploadFiles(upload_files).create_zip(upload_path)

        expected_files = sorted([
            Path(temp_path, '1/test_4.xyz'),
            Path(temp_path, '2/test_3.xyz'),
            Path(temp_path, '2/test_4.xyz'),
            Path(temp_path, '3/test_2.xyz'),
            Path(temp_path, '3/test_3.xyz'),
            Path(temp_path, '3/test_4.xyz'),
            Path(temp_path, '4/test_1.xyz'),
            Path(temp_path, '4/test_2.xyz'),
            Path(temp_path, '4/test_3.xyz'),
            Path(temp_path, '4/test_4.xyz'),
            Path(upload_path, 'upload_0.agora_upload'),
        ])

        expected_targets = sorted([
            '1/test_4.xyz',
            '2/test_3.xyz',
            '2/test_4.xyz',
            '3/test_2.xyz',
            '3/test_3.xyz',
            '3/test_4.xyz',
            '4/test_1.xyz',
            '4/test_2.xyz',
            '4/test_3.xyz',
            '4/test_4.xyz',
            'upload_0.agora_upload',
        ])

        expected_zipped_files = sorted([
            '0/test_0.xyz',
            '0/test_1.xyz',
            '0/test_2.xyz',
            '0/test_3.xyz',
            '0/test_4.xyz',
            '1/test_0.xyz',
            '1/test_1.xyz',
            '1/test_2.xyz',
            '1/test_3.xyz',
            '2/test_0.xyz',
            '2/test_1.xyz',
            '2/test_2.xyz',
            '3/test_0.xyz',
            '3/test_1.xyz',
            '4/test_0.xyz',
        ])

        assert sorted([f.file for f in result]) == expected_files
        assert sorted([f.target for f in result]) == expected_targets

        zip_file = next(f for f in result if f.target == 'upload_0.agora_upload')
        with zipfile.ZipFile(zip_file.file, 'r') as z:
            assert sorted([info.filename for info in z.infolist()]) == expected_zipped_files


class TestURLValidate:

    def test_url_validate(self):
        assert validate_url('https://gauss4.ethz.ch') == 'https://gauss4.ethz.ch'
        assert validate_url('http://gauss4.ethz.ch') == 'http://gauss4.ethz.ch'
        with pytest.raises(AgoraException):
            validate_url('gauss4.ethz.ch') == 'http://gauss4.ethz.ch'
        with pytest.raises(AgoraException):
            validate_url('gauss4.ethz.ch/') == 'http://gauss4.ethz.ch'
        assert validate_url('http://gauss4.ethz.ch/exam/1/') == 'http://gauss4.ethz.ch'
