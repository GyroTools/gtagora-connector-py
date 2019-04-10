# gtagora-connector [![Build Status](https://travis-ci.org/gyrofx/gtagora-connector-py.svg?branch=master)](https://travis-ci.org/gyrofx/gtagora-connector-py)

gtagora-connector is a python library to access GyroTools' Agora system.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install gtagora-connector.

```bash
pip install gtagora-connector
```

Currently gtagora-connector supports python 3.6 and 3.7.

## Usage

```python
from gtagora import Agora
from gtagora.models.dataset import DatasetType

agora = Agora.create('https://your.agora.domain.com', user='test', password='test')

root_folder = agora.get_folders()
subfolders = root_folder.get_folders() 
for s in subfolders:
    print(f' - {s.name}')
    
new_folder = root_folder.get_or_create_folder('New Folder')

exam = agora.get_exam_list(filters={'name': 'Wrist'})[0]
for s in exam.get_series():
    print(f'Series: {s.name}')
    
    for dataset in s.get_datasets(filters={'type': DatasetType.PHILIPS_RAW}):
        for datafile in dataset.get_datafiles():
            print(f'{datafile.original_filename}')

agora.import_data('/path/to/directroy', new_folder)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)