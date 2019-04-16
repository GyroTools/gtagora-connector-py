patient = {
            "id": 1,
            "permissions": {
                "write": True,
                "read": True
            },
            "most_recent_exam_date": "2016-04-21T13:43:13Z",
            "created_date": "2016-10-11T12:46:13Z",
            "modified_date": "2018-11-22T06:48:24Z",
            "name": "Daniel Smith",
            "patient_id": "HOSP2",
            "birth_date": "1980-12-05",
            "sex": "m",
            "weight": 72,
            "anonymous": False,
            "creator": None
        }


patient_list = {
            "count": 6,
            "limit": 10,
            "offset": 0,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T13:43:13Z",
                    "created_date": "2016-10-11T12:46:13Z",
                    "modified_date": "2018-11-22T06:48:24Z",
                    "name": "Daniel Smith",
                    "patient_id": "HOSP2",
                    "birth_date": "1980-12-05",
                    "sex": "m",
                    "weight": 72,
                    "anonymous": False,
                    "creator": None
                },
                {
                    "id": 2,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T10:58:16Z",
                    "created_date": "2016-10-11T12:57:32Z",
                    "modified_date": "2018-04-03T15:09:33Z",
                    "name": "Marcel Hoppe",
                    "patient_id": "HOSP1",
                    "birth_date": "1974-03-07",
                    "sex": "m",
                    "weight": 80,
                    "anonymous": False,
                    "creator": None
                },
                {
                    "id": 3,
                    "permissions": {
                        "write": True,
                        "read": True
                    },
                    "most_recent_exam_date": "2016-04-21T12:26:11Z",
                    "created_date": "2016-10-11T12:59:03Z",
                    "modified_date": "2016-10-28T12:31:37Z",
                    "name": "Stefan Meier",
                    "patient_id": "HOSP4",
                    "birth_date": "1976-12-08",
                    "sex": "m",
                    "weight": 71,
                    "anonymous": False,
                    "creator": None
                },
            ]
        }

task = {
        "id": 2,
        "inputs": [
            {
                "id": 2,
                "name": "input",
                "key": "in1",
                "description": "",
                "required": True,
                "order": 0,
                "type": 3,
                "data_set_type": 100000,
                "filename_regex": None,
                "min": None,
                "max": None,
                "select_values": None
            }
        ],
        "outputs": [],
        "members": [],
        "name": "notepad",
        "container_name": "",
        "container_options": {
            "mount_volumes": []
        },
        "execute_template": "notepad {{ inputs.in1.file.path }}",
        "execute_version": None,
        "success_exit_code": 0,
        "parse_output_for_error": "",
        "owner": 1,
        "host": None
    }
