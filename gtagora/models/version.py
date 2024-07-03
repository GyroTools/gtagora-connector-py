from gtagora.models.base import BaseModel
from packaging import version
from gtagora.exception import AgoraException


class Version(BaseModel):

    BASE_URL = '/api/v1/version/'

    def is_dev(self):
        return self.version.lower() == 'dev'

    def is_higher_than(self, other_version):
        return version.parse(self.version.replace('-SNAPSHOT', '')) > version.parse(other_version)

    def is_lower_than(self, other_version):
        return version.parse(self.version.replace('-SNAPSHOT', '')) < version.parse(other_version)

    def needs(self, version, feature=None, error_message=None):
        if not self.is_dev() and self.is_lower_than(version):
            if error_message:
                msg = error_message
            elif feature:
                msg = f'The {feature} feature needs Agora version {version} or higher. Please upgrade your Agora'
            else:
                msg = f'This feature needs Agora version {version} or higher. Please upgrade your Agora'
            raise AgoraException(msg)




