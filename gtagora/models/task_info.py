import datetime
import time

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel


class TaskInfo(BaseModel):
    BASE_URL = '/api/v1/task/'
    TIMEOUT = 60

    def join(self):
        return self.poll();

    def poll(self, interval=2):
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).seconds < self.TIMEOUT:
            task_info = self.get(self.id, http_client=self.http_client)

            if task_info.state == 0 or task_info.state == 1:
                time.sleep(interval)
                continue
            elif task_info.state == 2:
                return task_info
            elif task_info.state == 3:
                raise AgoraException(task_info.error)
            elif task_info.state.state == 4 or task_info.state.state == 5:
                return None

