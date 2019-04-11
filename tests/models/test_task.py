import string
from gtagora import Agora



class TestTask:

    def test_import(self, http_client):
        pass
         # A = Agora.create('http://127.0.0.1:8000', user='martin', password='martin')
         # tasks = A.load_tasks('../data/tasks/tasks.json')
         #
         # if tasks:
         #     task0 = tasks[0]
         #     name_bak = task0.name
         #     task0.name = 'python_interface'
         #     task0.save()
         #
         #     task0.name = name_bak
         #     task0.save()
         #
         #     task0 = tasks[0]
         #     task0.name = string.ascii_lowercase
         #     new_task = task0.create()
         #
         #     new_task.delete()
