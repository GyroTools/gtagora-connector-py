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

server = '<AGORA SERVER>'
api_key = '<YOUR_API_KEY>'

agora = Agora.create(server, api_key)

myagora_project = agora.get_myagora()
root_folder = myagora_project.get_root_folder()
subfolders = root_folder.get_folders()
for s in subfolders:
    print(f' - {s.name}')

new_folder = root_folder.get_or_create('New Folder')

exams = myagora_project.get_exams(filters={'name': 'Wrist'})
if exams:
    exam = exams[0]
    for s in exam.get_series():
        print(f'Series: {s.name}')

        for dataset in s.get_datasets(filters={'type': DatasetType.PHILIPS_RAW}):
            for datafile in dataset.get_datafiles():
                print(f'{datafile.original_filename}')

agora.import_data('/path/to/directroy', new_folder)
```

## Examples

### Create an Agora instance


```python
from gtagora import Agora

agora = Agora.create('https://your.agora.domain.com', user='test', password='test')
```

Since, it is not recommended to ever write down your password in plain text, Agora offers the possibility to connect with an API key. 
The API key can be activated in your Agora profile, and is a random UUID which can be withdrawn or recreated easily.


```python
from gtagora import Agora

agora = Agora.create('https://your.agora.domain.com', api_key='<YOUR_API_KEY>')
```

### Working with projects

Get a list of projects:

```python
projects = agora.get_projects()
for p in projects:
    print(f" - {p.display_name}")
```

Get a project by ID:

```python
project = agora.get_project(2)
print(f" - {project.display_name}")
```

Get the \"My Agora\" project:

```python
myagora = agora.get_myagora()
```

Get root folder of a project

```python
project = agora.get_project(2)
root_folder = project.get_root_folder()
```

Get all exams of a project

```python
project = agora.get_project(2)
exams = project.get_exams()
```

Empty the trash

```python
project = agora.get_project(2)
project.empty_trash()
```

### Working with folders

Get the root folder of the \"My Agora\" project:

```python
myagora = agora.get_myagora()
root_folder = myagora.get_root_folder()
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

Get a subfolder folder by name. None will be returned if the folder does not exist

```python
my_folder = folder.get_folder('my_folder')
```


The get_folder function also takes a relative path.

```python
my_folder = folder.get_folder('../../data/my_folder')
```

Create a new folder in the root folder (the new folder object is returned). An exception is thrown if a folder with the same name already exists.

```python
new_folder = root_folder.create_folder('TestFolder')
print(f"New folder ID: {new_folder.id}")
```

Get a folder or create a new one if it does not exist

```python
new_or_existing_folder = root_folder.get_or_create('TestFolder')
```

Delete a folder. Delete a folder is recursive. It deletes all items. The delete operation does not follow links.

```python
folder.delete()
```

    
Get all items of a folder. An item could for example be an exam, series or dataset

```python
items = folder.get_items()
for item in items:
    print(f" - {item}")
```

Get all exams of a folder. Use the recursive parameter to also get the exams in all subfolders 

```python
exams = folder.get_exams(recursive=False)
for exam in exams:
    print(f" - {exam}")
```

Get all datasets of a folder. Use the recursive parameter to also get the exams in all subfolders 

```python
datasets = folder.get_datasets(recursive=False)
```

Get a dataset by name. None is returned if the dataset does not exist

```python
dataset = folder.get_dataset('my_dataset')
```

Get the path of a folder within Agora (breadcrumb) 

```python
folder = agora.get_folder(45)
breadcrumb = folder.get_breadcrumb()
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

Get all series of an exam and then all datasets of the first series

```python
series = exam.get_series()
datasets = series[0].get_datasets()
```

Get all datasets of an exam 

```python
series = exam.get_datasets()
```

Get a list of all patients

```python
patients = agora.get_patients()
```

Get a patient by ID

```python
patient = agora.get_patient(15)
```

Get a series or dataset by ID

```python
series = agora.get_series(76)
dataset = agora.get_dataset(158)
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

Exams, series and datasets also have a download function

```python
downloaded_files = exam.download(target)
downloaded_files = series.download(target)
downloaded_files = dataset.download(target)
```

### Import data

Upload files into a folder

```python
from pathlib import Path

folder = agora.get_folder(45)
file1 = Path('C:/images/test1.jpg')
file2 = Path('C:/images/test2.jpg')
folder.upload([file1, file2])
```

Upload a whole folder structure

```python
from pathlib import Path

folder = agora.get_folder(45)
data = Path('C:/data/my_folder')
folder.upload([data])
```

Upload (and import) a rawfile and add an additional file to the the created series (Agora version > 6.3.0):

In this example a scanner rawfile and a textfile is uploaded. The rawfile will be imported into Agora and a Study and Series 
will be created. We can add the additional text file to the created Series by specifying the "relations" attribute in the 
upload function. The "relations" attribute is a dictionary whose key is the path to the rawfile and the value is a list 
of additional files which will be added to the created series:

```python
folder = agora.get_folder(45)

files = [
Path('C:/data/raw/rawfile.raw'),
Path('C:/data/raw/rawfile.lab'),
Path('C:/data/log/logfile.txt'),
]

relations = {
'C:/data/raw/rawfile.raw' : ['C:/data/log/logfile.txt']
}

folder.upload(files, relations=relations)
```

This also works when uploading a whole directory:

```python
folder = agora.get_folder(45)

dir = [Path('C:/data/')]

relations = {
'C:/data/raw/rawfile.raw' : ['C:/data/log/logfile.txt']
}

folder.upload(dir, relations=relations)
```
  

### Working with tasks

Get all tasks visible to the current user:

```python
tasks = agora.get_tasks()
```

Get a task by ID

```python
task = agora.get_task(13)
```

Run a task. <br/>
In this example the task has 2 inputs:

- A dataset with key "ds"
- An integer number with key "size"

The last line in the code sample waits for the task to finish
```python
task = agora.get_task(13)
target_folder = agora.get_folder(24)
dataset = agora.get_dataset(57)
taskinfo = task.run(target=target_folder, ds=dataset, size=1024)
taskinfo.join()
```

alternatively only the ID's of the Agora objects can be given as argument:
```python
taskinfo = task.run(target=target_folder, ds=23, size=1024)
```

the syntax to run the task can be printed to the console with the syntax function:
```python
task.syntax()
```


Save a task after it has been modified

```python
task = agora.get_task(13)
task.name = 'new_name'
task.save()
```

Delete a task

```python
task.delete()
```

Export all tasks into a json file

```python
agora.export_tasks('<output file>.json')
```

Import tasks from file (Experimental!)

```python
agora.import_tasks('<input file>.json')
```

### Working with parameters

Get a parameter by name

```python
dataset = agora.get_dataset(13)
parameter = dataset.get_parameter('EX_ACQ_echoes')
if not parameter.is_array:
    value = parameter.values[0]
else:
    value = parameter.values
```

Search for parameters

```python
dataset = agora.get_dataset(13)
parameters = dataset.search_parameter('EX_ACQ_')
print(f'{len(parameters)} parameters found')
```


### Users and sharing

Get the current user

```python
current_user = agora.get_current_user()
```

Get all users

```python
users = agora.get_users()
```

Get all user groups

```python
users = agora.get_groups()
```

### Various

The members of any Agora object can be printed to the console with the display function
```python
exam = agora.get_exam(22)
exam.display()

folder = agora.get_folder(15)
folder.display()
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
