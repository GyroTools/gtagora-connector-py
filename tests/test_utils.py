import zipfile
from pathlib import Path

import pytest

from gtagora.utils import get_file_info, ZipUploadFiles, to_path_array


def test_to_path_array():
    expected_output = [Path('files/test.xyz')]
    assert to_path_array('files/test.xyz') == expected_output
    assert to_path_array(['files/test.xyz']) == expected_output
    assert to_path_array(Path('files/test.xyz')) == expected_output
    assert to_path_array(expected_output) == expected_output

    expected_output = [Path('files/test.xyz'), Path('files/test.rrr')]
    assert to_path_array(['files/test.xyz', 'files/test.rrr']) == expected_output
    assert to_path_array(expected_output) == expected_output

    assert to_path_array([]) == []

    with pytest.raises(TypeError):
        assert to_path_array(12)

    with pytest.raises(TypeError):
        assert to_path_array(None)


def test_get_file_info(tempdir_with_dummy_files):
    temp_path = tempdir_with_dummy_files

    nof_files, total_size = get_file_info(temp_path)
    assert nof_files == 25
    assert total_size == 500

    nof_files, total_size = get_file_info(temp_path / '0/test_0.xyz')
    assert nof_files == 1
    assert total_size == 20


class TestZipUploadFiles:

    def _prepare_input_files_1(self, temp_path):
        input_files = []
        target_files = []

        for idx in range(0, 5):
            for subdir_idx in range(0, 5):
                p = temp_path / f'{subdir_idx}'
                p.mkdir(parents=True, exist_ok=True)
                file = p / f'test_{idx}.xyz'
                with open(file, 'wb') as f:
                    f.write(b'0123456789' * 1024 * (idx + 1) * (subdir_idx + 1))
                    input_files.append(file.as_posix())
                    target_files.append(file.relative_to(temp_path).as_posix())

        return input_files, target_files

    def test_create_zip_1(self, tmpdir):
        temp_path = Path(tmpdir)

        upload_dir = temp_path / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)

        input_files, target_files = self._prepare_input_files_1(temp_path)
        zip_uploads = ZipUploadFiles(input_files, target_files)
        final_input_files, final_target_files = zip_uploads.create_zip(upload_dir.as_posix())

        assert final_input_files == [Path(upload_dir, 'upload_0.agora_upload').as_posix()]
        assert final_target_files == ['upload_0.agora_upload']

        zip_file_path = final_input_files[0]
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            assert len(z.infolist()) == 25
            assert [info.filename for info in z.infolist()] == target_files

    def test_create_zip_2(self, tmpdir):
        temp_path = Path(tmpdir)

        upload_dir = temp_path / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)

        ZipUploadFiles.MAX_FILE_LIMIT = 100*1024  # Zip all files smaller than 100 KB

        input_files, target_files = self._prepare_input_files_1(temp_path)
        zip_uploads = ZipUploadFiles(input_files, target_files)
        final_input_files, final_target_files = zip_uploads.create_zip(upload_dir.as_posix())

        expected_input_files = sorted([
            Path(temp_path, '1/test_4.xyz').as_posix(),
            Path(temp_path, '2/test_3.xyz').as_posix(),
            Path(temp_path, '2/test_4.xyz').as_posix(),
            Path(temp_path, '3/test_2.xyz').as_posix(),
            Path(temp_path, '3/test_3.xyz').as_posix(),
            Path(temp_path, '3/test_4.xyz').as_posix(),
            Path(temp_path, '4/test_1.xyz').as_posix(),
            Path(temp_path, '4/test_2.xyz').as_posix(),
            Path(temp_path, '4/test_3.xyz').as_posix(),
            Path(temp_path, '4/test_4.xyz').as_posix(),
            Path(upload_dir, 'upload_0.agora_upload').as_posix(),
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


