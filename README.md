# gtagora-connector [![Build Status](https://travis-ci.org/gyrofx/gtagora-connector-py.svg?branch=master)](https://travis-ci.org/gyrofx/gtagora-connector-py)

gtagora-connector is a python library to access GyroTools' Agora system.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install gtagora-connector.

```bash
pip install gtagora-connector
```

Currently gtagora-connector supports python 3.6 and 3.7.

## Basic usage

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

## Exmaples

### Create an Agora instanace


```python
from gtagora import Agora

agora = Agora.create('https://your.agora.domain.com', user='test', password='test')
```

Because it's not recommended to ever write down your password in plain text the API is a better alternative. Actiavte the API Key in your Agora profile. The API key is just a random UUID and it can withdrawn or recreated easily.

```python
from gtagora import Agora

agora = Agora.create('https://your.agora.domain.com', api_key='<YOUR_API_KEY>')
```

### Working with folders

Get the root folder of the current user:

```python
root_folder = agora.get_root_folder()
print(f"Root folder ID: {root_folder.id}")
```

Get a folder by its ID

```python
folder = agora.get_folder(45)
print(f"Folder with ID {folder.name}")
```

Get sub folders

```python
subfolders = folder.get_folders()
for f in subfolders:
    print(f" - {f.name}")
```

Create a new folder in the root folder (the new folder object is returned)

```python
new_folder = root_folder.create_folder('TestFolder')
print(f"New folder ID: {new_folder.id}")
```

Delete a folder. Delete a folder is recursive. It deletes all items. The delete operation does not follow links.

```python
folder.delete()
```

    
Get all items of a folder. An item could be a exam, series or a dataset

```python
items = folder.get_items()
for item in items:
    print(f" - {item}")
```

Get all exams of a folder. Use the recursive parameter to get all exams 

```python
exams = folder.get_exams(recursive=False)
for exam in exams:
    print(f" - {exam}")
```
    
### Working with Agora objects

Get the list of exams

```python
exams = agora.get_exam_list()
```

Get an exam by ID

```python
exam = agora.get_exam(12)
```

Link the first Exam to the a folder

```python
exam_item = exam.link_to_folder(folder.id)
```

Delete the link of an exam (doesn't delete the Exam itself)

```python
exam_item.delete()
```

### Download data

Download all data from a folder 

```python
from pathlib import Path

target = Path("c:/temp")
downloaded_files = folder.download(target, recursive=False)
for f in downloaded_files:
    print(str(f))
```


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)