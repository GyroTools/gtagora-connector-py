from gtagora import Agora
from gtagora.models.task import Task, ScriptTask
from tests.models import data
from tests.helper import FakeResponse

from pathlib import Path


class TestTask:
    def test_get(self, http_client):
        http_client.set_next_response(FakeResponse(200, data.task))

        t = Task.get(2, http_client=http_client)

        assert isinstance(t, Task)
        assert t.id == 2
        assert t.name == "notepad"

    def test_load(self, http_client):
        task_file = Path(__file__).parent / '../data/tasks/tasks.json'
        http_client.set_next_response(FakeResponse(200, data.version))
        A = Agora(http_client)
        tasks = A.load_tasks(task_file.as_posix())

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
        assert task0.execute_version is None
        assert task0.success_exit_code == 0
        assert task0.parse_output_for_error == ''
        assert task0.owner == 1
        assert task0.host is None


class TestScriptTask:
    def test_set_values_parses_inputs(self):
        t = ScriptTask.from_response(data.script_task)

        assert hasattr(t, 'inputs')
        assert len(t.inputs) == 3
        keys = [i['key'] for i in t.inputs]
        assert 'in1' in keys
        assert 'in2' in keys
        assert 'in3' in keys

        in1 = next(i for i in t.inputs if i['key'] == 'in1')
        assert in1['type'] == Task.INPUT_TYPE_DATASET
        assert in1['required'] is True

        in2 = next(i for i in t.inputs if i['key'] == 'in2')
        assert in2['type'] == Task.INPUT_TYPE_INTEGER
        assert in2['required'] is False

        in3 = next(i for i in t.inputs if i['key'] == 'in3')
        assert in3['type'] == Task.INPUT_TYPE_EXAM  # 'study' maps to EXAM

    def test_set_values_sets_outputs(self):
        t = ScriptTask.from_response(data.script_task)
        assert hasattr(t, 'outputs')
        assert t.outputs == []

    def test_syntax(self, capsys):
        t = ScriptTask.from_response(data.script_task)
        t.syntax()
        captured = capsys.readouterr()
        assert 'in1' in captured.out
        assert 'in2' in captured.out
        assert 'in3' in captured.out

    def test_run(self, http_client):
        t = ScriptTask.from_response(data.script_task, http_client=http_client)
        http_client.set_next_response(FakeResponse(200, data.timeline_item))

        result = t.run(in1=42, in2=5, in3=7)

        last = http_client.requests[-1]
        assert last['url'] == '/api/v2/taskdefinition_yaml/10/run/'
        assert last['data']['inputs']['in1'] == {'object_id': 42, 'object_type': 'dataset'}
        assert last['data']['inputs']['in2'] == 5
        assert last['data']['inputs']['in3'] == {'object_id': 7, 'object_type': 'exam'}
        assert result is not None
