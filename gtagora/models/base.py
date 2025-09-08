import pprint
import re
import unicodedata

from gtagora.exception import AgoraException


def get_client(http_client):
    from gtagora import Agora

    return http_client if http_client else Agora.default_client


class BaseModel:

    BASE_URL = ''
    BASE_URL_V2 = ''

    V2_DEFAULT = False

    def __init__(self, http_client=None):
        self.http_client = get_client(http_client)

    @property
    def base_url(self):
        return self.BASE_URL_V2 if self.V2_DEFAULT else self.BASE_URL

    @classmethod
    def get_base_url(cls):
        return cls.BASE_URL_V2 if cls.V2_DEFAULT else cls.BASE_URL

    @classmethod
    def from_response(cls, model_dict, http_client=None):
        instance = cls(http_client=http_client)
        instance._set_values(model_dict)

        return instance

    @classmethod
    def get(cls, id=None, http_client=None):
        instance = cls(http_client=http_client)
        return instance._get_object(id)

    @classmethod
    def get_list(cls, filters=None, http_client=None):
        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        instance = cls(http_client=http_client)
        filters = filters if filters else {}
        if 'limit' not in filters:
            filters['limit'] = '10000000000'

        url = cls.get_base_url()
        return instance._get_object_list(url, filters, cls)

    @classmethod
    def get_list_from_data(cls, data):
        object_list = []

        if 'results' in data and 'count' in data:
            results = data['results']
            if data['count'] == 0:
                return object_list
            if data['count'] != len(results):
                print('Warning: Could not get all series')

            for r in results:
                object_list.append(cls.from_response(r))
        elif isinstance(data, list):
            object_list = [cls.from_response(d) for d in data]

        return object_list

        raise AgoraException(f'Could not get the {cls.__name__} list')

    def delete(self):
        url = f'{self.base_url}{self.id}/'
        response = self.http_client.delete(url)

        if response.status_code == 204:
            return True
        raise AgoraException('Could not delete FolderItem')

    def to_valid_filename(self, value, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    def to_dict(self):
        excluded_keys = ['http_client']
        return dict( (key, value) for (key, value) in self.__dict__.items() if key not in excluded_keys and not key.startswith('__'))

    def content_type(self):
        from gtagora.models.dataset import Dataset
        from gtagora.models.exam import Exam
        from gtagora.models.folder import Folder
        from gtagora.models.patient import Patient
        from gtagora.models.series import Series

        if isinstance(self, Exam):
            return 'exam'
        elif isinstance(self, Folder):
            return 'folder'
        elif isinstance(self, Series):
            return 'serie'
        elif isinstance(self, Dataset):
            return 'dataset'
        elif isinstance(self, Patient):
            return 'patient'

    def _set_values(self, model_dict):
        for key, value in model_dict.items():
            setattr(self, key, value)

    def _get_object(self, id):
        if id:
            url = f'{self.base_url}{id}/'
        else:
            url = f'{self.base_url}'

        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return self.__class__.from_response(data, http_client=self.http_client)

        raise AgoraException('Could not get the {0}. HTTP status = {1}'.format(self.__class__.__name__, response.status_code))

    def _get_object_list(self, url, params, object_class):
        response = self.http_client.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            object_list = []

            if 'results' in data and 'count' in data:
                results = data['results']
                if data['count'] == 0:
                    return object_list
                if data['count'] != len(results):
                    print('Warning: Could not get all series')

                for r in results:
                    object_list.append(object_class.from_response(r))
            elif isinstance(data, list):
                object_list = [object_class.from_response(d) for d in data]
            else:
                return object_class.from_response(data)

            return object_list

        raise AgoraException(f'Could not get the {object_class.__name__} list')

    def display(self):
        pprint.pprint(vars(self), indent=4)


class DownloadDatasetMixin:

    def download(self, filename):
        datasets = self.get_datasets()
        return [dataset.download(filename) for dataset in datasets]


class LinkToFolderMixin:
    def link_to_folder(self, folder):
        from gtagora.models.folder import Folder
        from gtagora.models.folder_item import FolderItem

        if isinstance(folder, Folder):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise AgoraException('The input must either be a folder or a folder id')

        url = f'{self.base_url}{self.id}/link_to/{folder_id}/'
        post_data = {}
        response = self.http_client.post(url, post_data)
        if response.status_code == 201:
            return FolderItem.from_response(response.json(), http_client=self.http_client)

        raise AgoraException('Could not create a link')

    def get_folders(self, parent_folder = None, filters=None):
        from gtagora.models.folder import Folder

        if filters and not isinstance(filters, dict):
            raise AgoraException('The filter must be a dict')

        url = f'{self.base_url}{self.id}/folders/?limit=10000000000'

        folders = self._get_object_list(url, filters, Folder)

        if parent_folder:
            filtered_folders = []
            for f in folders:
                if f.is_subfolder_of(parent_folder):
                    filtered_folders.append(f)

            folders = filtered_folders if filtered_folders else None

        return folders

    def is_in_folder(self, object: BaseModel, folder):
        from gtagora.models.folder import Folder

        folder_id = None
        if isinstance(folder, Folder):
            folder_id = folder.id
        elif isinstance(folder, int):
            folder_id = folder
        else:
            raise AgoraException('The folder argument must either be a Folder class or a folder ID')

        folders = object.get_folders()
        for f in folders:
            breadcrumb = f.get_breadcrumb()
            for b in breadcrumb:
                if b.object_id == folder_id:
                    return f

        return None


class SearchMixin:

    @classmethod
    def search(cls, search_string, http_client=None):
        instance = cls(http_client=http_client)

        if not isinstance(search_string, str):
            raise AgoraException('The search term must be a string')

        url = f'{instance.base_url}search/?q=' + search_string + '&limit=10000000000'
        response = http_client.get(url)
        if response.status_code == 200:
            list = instance.get_list_from_data(response.json())
            return list
        else:
            raise AgoraException(f'Search unsuccessful: {response.text}')

        return []


class TagMixin:
    def tag(self, tag):
        from gtagora.models.tag import Tag, TagInstance

        if isinstance(tag, Tag):
            tag_id = tag.id
        elif isinstance(tag, int):
            tag_id = tag
        else:
            raise AgoraException('The input must either be a tag or a tag id')

        url = TagInstance.get_base_url()
        post_data = {'tag_definition': tag_id, 'tagged_object_content_type': self.content_type(), 'tagged_object_id': self.id}
        response = self.http_client.post(url, post_data)
        if response.status_code == 201:
            instances = TagInstance.get_list_from_data(response.json())
            if instances:
                return instances[0]
            else:
                return None

        raise AgoraException('Could not tag the object')

    def get_tags(self):
        from gtagora.models.tag import Tag

        url = f'{self.BASE_URL_V2}{self.id}/tags/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            list = Tag.get_list_from_data(response.json())
            return list
        else:
            raise AgoraException(f'Cannot get the tags: {response.text}')

    def remove_tag(self, tag):
        from gtagora.models.project import Project
        from gtagora.models.tag import Tag, TagInstance

        if not isinstance(tag, Tag):
            raise AgoraException('The input must be a Tag class')

        # at the moment we don't have the possibility to get a tag-instance for an object. So we have to get all
        # tag-instances for the project and then search for the object
        project = tag.project if tag.project else self.project if hasattr(self, 'project') else None        
        if not project:
            url = TagInstance.get_base_url()             
        else:
            url = Project.get_base_url() + f'{project}/tag-instance/'
           
        response = self.http_client.get(url)
        if response.status_code == 200:
            tag_instances = TagInstance.get_list_from_data(response.json())
            tag_instance = next((x for x in tag_instances if x.tag_definition == tag.id and x.tagged_object_id == self.id), None)
            if not tag_instance:
                raise AgoraException(f'The object is not tagged with the tag "{tag.label}"')
            url = TagInstance.get_base_url() + f'{tag_instance.id}/'
            response = self.http_client.delete(url)
            if response.status_code == 204:
                return True
            else:
                raise AgoraException(f'Could not remove the tag: {response.text}')


class RatingMixin:
    def rate(self, value):
        from gtagora.models.tag import RatingInstance

        if value < 0 or value > 5:
            raise AgoraException('The rating must be between 0 and 5')

        # check if the object already has a rating
        rating = self.get_rating()
        url = RatingInstance.BASE_URL

        if rating:
            if value == 0:
                # delete rating
                response = self.http_client.delete(f'{url}{rating.id}/')
            else:
                # update rating
                put_data = {'id': rating.id, 'value': value, 'rated_object_content_type': self.content_type(), 'rated_object_id': self.id}
                response = self.http_client.put(f'{url}{rating.id}/', put_data)
        else:
            # create rating
            post_data = {'value': value, 'rated_object_content_type': self.content_type(), 'rated_object_id': self.id}
            response = self.http_client.post(url, post_data)

        if response.status_code == 204:
            return None

        if response.status_code < 400:
            return RatingInstance.from_response(response.json(), http_client=self.http_client)

        raise AgoraException('Could not rate the object')

    def get_rating(self):
        from gtagora.models.tag import RatingInstance

        url = f'{self.BASE_URL_V2}{self.id}/rating/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            ratings = RatingInstance.get_list_from_data(response.json())
            if ratings:
                return ratings[0]
            else:
                return None


        raise AgoraException(f'Cannot get the rating: {response.text}')


class RelationMixin:
    def relations(self):
        url = f'{self.BASE_URL}{self.id}/datarelations/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            if not response.json() or not isinstance(response.json(), list) or len(response.json()) == 0:
                return []
            relations = []
            for relation in response.json():
                object = None
                if relation.get('from_object', {}).get('object_id') == self.id:
                    object = relation.get('to_object')
                elif relation.get('to_object', {}).get('object_id') == self.id:
                    object = relation.get('from_object')
                if object:
                    id = object.get('object_id', None)
                    if not id:
                        continue
                    instance = self.get(id, http_client=self.http_client)
                    if instance:
                        relations.append(instance)
                else:
                    continue
            return relations
        else:
            raise AgoraException(f'Cannot get the relations: {response.text}')