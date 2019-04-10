from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.dataset import Dataset
from gtagora.models.exam import Exam
from gtagora.models.series import Series


class FolderItem(BaseModel):
    BASE_URL = '/api/v1/folderitem/'

    def _set_values(self, model_dict):
        from gtagora.models.folder import Folder

        for key, value in model_dict.items():
            if key == 'content_object':
                content_object = model_dict['content_object']
            else:
                setattr(self, key, value)

        if self.content_type == 'folder':
            self.object = Folder.from_response(content_object, http_client=self.http_client)
        elif self.content_type == 'exam':
            self.object = Exam.from_response(content_object, http_client=self.http_client)
        elif self.content_type == 'serie':
            self.object = Series.from_response(content_object, http_client=self.http_client)
        elif self.content_type == 'dataset':
            self.object = Dataset.from_response(content_object, http_client=self.http_client)

    def __str__(self):
        return f"FolderItem {self.id}, {self.content_type}, {self.object.name}"
