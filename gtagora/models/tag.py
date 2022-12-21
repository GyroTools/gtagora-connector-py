from gtagora.models.base import BaseModel


class Tag(BaseModel):

    BASE_URL = '/api/v2/tag-definition/'


class TagInstance(BaseModel):

    BASE_URL = '/api/v2/tag-instance/'
