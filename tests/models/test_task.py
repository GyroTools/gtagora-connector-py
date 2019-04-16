from gtagora import Agora
from gtagora.models.task import Task
from tests.models import data
from tests.helper import FakeResponse


class TestTask:
     def test_get(self, http_client):
          http_client.set_next_response(FakeResponse(200, data.task))

          t = Task.get(2, http_client=http_client)

          assert isinstance(t, Task)
          assert t.id == 2
          assert t.name == "notepad"

     def test_load(self, http_client):
          A = Agora('dummy')
          tasks = A.load_tasks('../data/tasks/tasks.json')

          assert len(tasks) == 4

          task0 = tasks[0]
          assert hasattr(task0, 'id')
          assert hasattr(task0, 'inputs')
          assert hasattr(task0, 'outputs')
          assert hasattr(task0, 'members')
          assert hasattr(task0, 'name')
          assert hasattr(task0, 'container_name')
          assert hasattr(task0, 'container_options')
          assert hasattr(task0, 'execute_template')
          assert hasattr(task0, 'execute_version')
          assert hasattr(task0, 'success_exit_code')
          assert hasattr(task0, 'parse_output_for_error')
          assert hasattr(task0, 'owner')
          assert hasattr(task0, 'host')

          assert task0.id == 2
          assert task0.outputs == []
          assert task0.members == []
          assert task0.members == []
          assert task0.name == 'notepad'
          assert task0.container_name == ''
          assert task0.execute_template == 'notepad {{ inputs.in1.file.path }}'
          assert task0.execute_version == None
          assert task0.success_exit_code == 0
          assert task0.parse_output_for_error == ''
          assert task0.owner == 1
          assert task0.host == None


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
