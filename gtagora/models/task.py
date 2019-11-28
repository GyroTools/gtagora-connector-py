import json

from gtagora.exception import AgoraException
from gtagora.models.base import BaseModel
from gtagora.models.task_info import TaskInfo


class Task(BaseModel):

    BASE_URL = '/api/v1/taskdefinition/'

    INPUT_TYPE_EXAM = 1
    INPUT_TYPE_SERIES = 2
    INPUT_TYPE_DATASET = 3
    INPUT_TYPE_FILE = 4
    INPUT_TYPE_STRING = 5
    INPUT_TYPE_INTEGER = 6
    INPUT_TYPE_FLOAT = 7
    INPUT_TYPE_SELECT = 8
    INPUT_TYPE_FOLDER = 9

    def run(self, input=None, target: BaseModel=None, **kwargs):
        if input:
            input_dict = self._get_inputs(input)
        else:
            input_dict = self._get_inputs(kwargs)
        self._check_outputs(target)

        data = {}

        if target:
            object_name = target.__class__.__name__.lower()
            data['target'] = {'object_id': target.id, 'object_type': object_name}
        else:
            data['target'] = None

        data['inputs'] = input_dict

        url = f'{self.BASE_URL}{self.id}/run/'
        response = self.http_client.post(url, json=data, timeout=60)

        if response.status_code != 200:
            raise AgoraException('Cannot run the task: ' + response.text)
        else:
            taskinfo = json.loads(response.content)
            result = TaskInfo.get_list_from_data([taskinfo])
            return result[0] if result else None

    def create(self):
        data = self.toDict()
        data['id'] = None
        if 'inputs' in data and data['inputs']:
            for input in data['inputs']:
                if 'id' in input:
                    input['id'] = None
        response = self.http_client.post(self.BASE_URL, json=data, timeout=60)
        if response.status_code != 201:
            raise AgoraException('Cannot create a task: ' + response.text)
        else:
            created_task = json.loads(response.content)
            result = self.get_list_from_data([created_task])
            return result[0] if result else None


    def save(self):
        if not hasattr(self, 'id') or not self.id:
            self.create()
        else:
            url = f'{self.BASE_URL}{self.id}/'
            data = self.toDict()
            response = self.http_client.put(url, json=data, timeout=60)
            if response.status_code != 200:
                raise AgoraException('Cannot create a task: ' + response.text)

    def delete(self):
        if not hasattr(self, 'id') or not self.id:
            raise AgoraException('Cannot delete the task: No ID available')
        else:
            url = f'{self.BASE_URL}{self.id}/'
            response = self.http_client.delete(url, timeout=60)
            if response.status_code != 204:
                raise AgoraException('Cannot delete the task: ' + response.text)

    def toDict(self):
        fields = ['container_name', 'container_options', 'execute_template', 'host', 'host_id', 'id', 'inputs', 'members', 'mount_volumes', 'name', 'outputs', 'parse_output_for_error', 'success_exit_code', 'task_target', 'use_docker']

        d = dict()
        for field in fields:
            d[field] = self.__dict__.get(field)

        return d

    def syntax(self):
        print(self._get_run_cmd())

    def _get_run_cmd(self):
        cmd = 'task.run('
        alternate_cmd = 'task.run('
        first = True
        for input in self.inputs:
            if not first:
                cmd += ', '
                alternate_cmd += ', '

            cmd += input['key'] + '=<' + self._get_type_name(input['type']) + '>'
            if input['type'] < 5:
                alternate_cmd += input['key'] + '=<' + self._get_type_name(input['type']) + ' ID>'
            else:
                alternate_cmd += input['key'] + '=<' + self._get_type_name(input['type']) + '>'

            first = False

        if self.outputs:
            if not first:
                cmd += ', '
                alternate_cmd += ', '
            cmd += 'target=<target>'
            alternate_cmd += 'target=<target>'
        cmd += ')'
        alternate_cmd += ')'
        return cmd + '\nOR\n' + alternate_cmd

    def _get_inputs(self, arguments):
        input_dict = {}
        for input in self.inputs:
            if not input['key'] in arguments:
                raise AgoraException('\n\nThe task input \'' + input['key'] + '\' is unassigned.\nRun the task with the following command:\n\n' + self._get_run_cmd())

            argument_name = input['key']
            argument = arguments[argument_name]
            argument_type = argument.__class__.__name__.lower()
            input_type = self._get_type_name(input['type'])
            if isinstance(argument, BaseModel):
                if argument_type != self._get_type_name(input['type']):
                    self._raise_input_error(input)
                input_dict[argument_name] = {'object_id': argument.id, 'object_type': argument_type}

            elif input['type'] < Task.INPUT_TYPE_STRING or input['type'] == Task.INPUT_TYPE_FOLDER:
                if not isinstance(argument, int):
                    self._raise_input_error(input)
                input_dict[argument_name] = {'object_id': argument, 'object_type': input_type}
            elif input['type'] == Task.INPUT_TYPE_STRING:
                if not isinstance(argument, str):
                    self._raise_input_error(input)
                input_dict[argument_name] = argument
            elif input['type'] == Task.INPUT_TYPE_INTEGER:
                if not isinstance(argument, int):
                    self._raise_input_error(input)
                input_dict[argument_name] = argument
            elif input['type'] == Task.INPUT_TYPE_FLOAT:
                if not isinstance(argument, float):
                    self._raise_input_error(input)
                input_dict[argument_name] = argument

        return input_dict

    def _check_outputs(self, target):
        if self.outputs and not target:
            raise AgoraException('\n\nThe \'target\' argument is missing (e.g. the output folder). Run the task with the following command:\n\n' + self._get_run_cmd())

        if self.outputs and not isinstance(target, BaseModel):
            raise AgoraException('\n\nThe target must be an Agora object (e.g. a folder)')

    def _raise_input_error(self, input):
        argument_name = input['key']
        argument_type = self._get_type_name(input['type'])
        msg = ''
        if input['type'] < Task.INPUT_TYPE_STRING or input['type'] == Task.INPUT_TYPE_FOLDER:
            msg += '\n\nThe task input \'' + argument_name + '\' must eihter be a ' + argument_type + ' or a ' + argument_type + ' ID'
        else:
            msg += '\n\nThe task input \'' + argument_name + '\' must be a ' + argument_type

        msg += '\n\nRun the task with the following syntax:\n' + self._get_run_cmd()

        raise AgoraException(msg)



    @staticmethod
    def _get_type_name(type: int):
        if type == 0:
            return 'none'
        elif type == Task.INPUT_TYPE_EXAM:
            return 'exam'
        elif type == Task.INPUT_TYPE_SERIES:
            return 'series'
        elif type == Task.INPUT_TYPE_DATASET:
            return 'dataset'
        elif type == Task.INPUT_TYPE_FOLDER:
            return 'folder'
        elif type == Task.INPUT_TYPE_STRING:
            return 'string'
        elif type == Task.INPUT_TYPE_INTEGER:
            return 'integer'
        elif type == Task.INPUT_TYPE_FLOAT:
            return 'float'
        elif type == Task.INPUT_TYPE_SELECT:
            return 'select'

