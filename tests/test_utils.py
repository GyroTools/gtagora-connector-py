import zipfile
from pathlib import Path

from gtagora.utils import get_file_info, ZipUploadFiles, validate_url


def test_get_file_info(tempdir_with_dummy_files):
    temp_path = tempdir_with_dummy_files

    nof_files, total_size = get_file_info(temp_path)
    assert nof_files == 25
    assert total_size == 500

    nof_files, total_size = get_file_info(temp_path / '0/test_0.xyz')
    assert nof_files == 1
    assert total_size == 20


class TestZipUploadFiles:

    def test_create_zip_1(self, zip_upload_files_test_data):
        test_data = zip_upload_files_test_data
        input_files = test_data.input_files
        target_files = test_data.target_files
        upload_path = test_data.upload_path

        zip_uploads = ZipUploadFiles(input_files, target_files)
        final_input_files, final_target_files = zip_uploads.create_zip(upload_path)

        assert final_input_files == [Path(upload_path, 'upload_0.agora_upload')]
        assert final_target_files == ['upload_0.agora_upload']

        zip_file_path = final_input_files[0]
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            assert len(z.infolist()) == 25
            assert [info.filename for info in z.infolist()] == target_files

    def test_create_zip_2(self, zip_upload_files_test_data):
        test_data = zip_upload_files_test_data
        temp_path = test_data.temp_path
        input_files = test_data.input_files
        target_files = test_data.target_files
        upload_path = test_data.upload_path

        ZipUploadFiles.MAX_FILE_LIMIT = 100*1024  # Zip all files smaller than 100 KB

        zip_uploads = ZipUploadFiles(input_files, target_files)
        final_input_files, final_target_files = zip_uploads.create_zip(upload_path)

        expected_input_files = sorted([
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

        expected_target_files = sorted([
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

        assert sorted(final_input_files) == expected_input_files
        assert sorted(final_target_files) == expected_target_files

        zip_file_path = final_input_files[0]
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            assert sorted([info.filename for info in z.infolist()]) == expected_zipped_files


class TestURLValidate:

    def test_url_validate(self):
        assert validate_url('https://gauss4.ethz.ch') == 'https://gauss4.ethz.ch'
        assert validate_url('http://gauss4.ethz.ch') == 'http://gauss4.ethz.ch'
        assert validate_url('gauss4.ethz.ch') == 'http://gauss4.ethz.ch'
        assert validate_url('gauss4.ethz.ch/') == 'http://gauss4.ethz.ch'
        assert validate_url('http://gauss4.ethz.ch/exam/1/') == 'http://gauss4.ethz.ch'
