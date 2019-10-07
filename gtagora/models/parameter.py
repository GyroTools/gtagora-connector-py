from gtagora.models.base import BaseModel


class Parameter(BaseModel):
    def __init__(self, http_client):
        super().__init__(http_client)
