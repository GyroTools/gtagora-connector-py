from gtagora.models.base import BaseModel


class ImageInfo(BaseModel):
    def __init__(self, http_client):
        super().__init__(http_client)
