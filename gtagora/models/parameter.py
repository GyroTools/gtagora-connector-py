from gtagora.models.base import BaseModel


class Parameter(BaseModel):
    def __init__(self, http_client):
        super().__init__(http_client)

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return False
        return self.Name == other.Name and self.Value == other.Value
