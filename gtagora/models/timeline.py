import datetime
import time

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class TimelineItem(BaseModel):
    BASE_URL = '/api/v2/timeline/'
    TIMEOUT = 60

    def join(self):
        return self.poll()

    def poll(self, interval=2):
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < self.TIMEOUT:
            timeline = self.get(self.id, http_client=self.http_client)

            state = timeline.data.get('state')
            if state:
                if state == 0 or state == 1:
                    time.sleep(interval)
                    continue
                elif state == 2:
                    return timeline
                elif state == 3:
                    raise AgoraException(timeline.error)
                elif state == 4 or state == 5:
                    return None
            else:
                return None

