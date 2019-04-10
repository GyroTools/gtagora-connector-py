import os
from pathlib import Path


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
