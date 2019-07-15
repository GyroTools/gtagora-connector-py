from gtagora.exception import AgoraException
from gtagora.models.share import ShareLevel


def get_client(http_client):
    from gtagora import Agora

    return http_client if http_client else Agora.default_client


class BaseModel:

    BASE_URL = ''

    def __init__(self, http_client=None):
        self.http_client = get_client(http_client)

    @classmethod
    def from_response(cls, model_dict, http_client=None):
        instance = cls(http_client=http_client)
        instance._set_values(model_dict)

        return instance

    @classmethod
    def get(cls, id, http_client=None):
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

        url = cls.BASE_URL
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
        url = f'{self.BASE_URL}{self.id}/'
        response = self.http_client.delete(url)

        if response.status_code == 204:
            return True
        raise AgoraException('Could not delete FolderItem')

    def _set_values(self, model_dict):
        for key, value in model_dict.items():
            setattr(self, key, value)

    def _get_object(self, id):
        url = f'{self.BASE_URL}{id}/'
        response = self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            return self.__class__.from_response(data, http_client=self.http_client)

        raise AgoraException('Could not get the {0}'.format(__class__.__name__))

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

            return object_list

        raise AgoraException(f'Could not get the {object_class.__name__} list')


class DownloadDatasetMixin:

    def download(self, filename):
        datasets = self.get_datasets()
        return [dataset.download(filename) for dataset in datasets]


class LinkToFolderMixin:
    def link_to_folder(self, folder_id):
        from gtagora.models.folder_item import FolderItem

        url = f'{self.BASE_URL}{self.id}/link_to/{folder_id}/'
        post_data = {}
        response = self.http_client.post(url, post_data)
        if response.status_code == 201:
            return FolderItem.from_response(response.json(), http_client=self.http_client)

        raise AgoraException('Could not create a link')


class ShareMixin:

    def share(self, user_id=None, group_id=None, share_level=ShareLevel.READ_ONLY):
        if not user_id and not group_id:
            raise AgoraException('Please specify a user id or group id')

        url = f'{self.BASE_URL}/{self.id}/shares/'
        data = [{"user": user_id, "group": group_id, "level": share_level}]
        response = self.http_client.post(url, json=data)
        return response


class SearchMixin:

    @classmethod
    def search(cls, search_string, http_client=None):
        instance = cls(http_client=http_client)

        if not isinstance(search_string, str):
            raise AgoraException('The search term must be a string')

        url = f'{instance.BASE_URL}search/?q=' + search_string + '&limit=10000000000'
        response = http_client.get(url)
        if response.status_code == 200:
            list = instance.get_list_from_data(response.json())
            return list
        else:
            raise AgoraException(f'Search unsuccessful: {response.text}')

        return []
