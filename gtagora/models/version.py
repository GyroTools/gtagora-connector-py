from gtagora.models.base import BaseModel
from distutils.version import LooseVersion
from gtagora.exception import AgoraException


class Version(BaseModel):

    BASE_URL = '/api/v1/version/'

    def is_dev(self):
        return self.version == 'DEV'

    def is_higher_than(self, version):
        return LooseVersion(self.version) > LooseVersion(version)

    def is_lower_than(self, version):
        return LooseVersion(self.version) < LooseVersion(version)

    def needs(self, version, feature=None, error_message=None):
        if not self.is_dev() and self.is_lower_than(version):
            if error_message:
                msg = error_message
            elif feature:
                msg = f'The {feature} feature needs Agora version {version} or higher. Please upgrade your Agora'
            else:
                msg = f'This feature needs Agora version {version} or higher. Please upgrade your Agora'
            raise AgoraException(msg)




