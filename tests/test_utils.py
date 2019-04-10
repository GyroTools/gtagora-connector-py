from gtagora.utils import get_file_info


def test_get_file_info(tempdir_with_dummy_files):
    temp_path = tempdir_with_dummy_files

    nof_files, total_size = get_file_info(temp_path)
    assert nof_files == 25
    assert total_size == 500

    nof_files, total_size = get_file_info(temp_path / '0/test_0.xyz')
    assert nof_files == 1
    assert total_size == 20
