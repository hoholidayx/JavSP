from webserver.ResponseData import ResponseData
from webserver.task.TaskService import TaskService


class TaskController:

    def __init__(self):
        self._taskService = TaskService()

    def start_task(self, json_data: dict):
        resp_data = {}
        if json_data and 'movie_dvdid' in json_data:
            for movie_dvdid in json_data['movie_dvdid']:
                task = self._taskService.start_task(movie_dvdid)
                if task:
                    resp_data[movie_dvdid] = {"task_id": task.id}
                else:
                    resp_data[movie_dvdid] = {}
            return ResponseData(data=resp_data)
        else:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED, msg='Invalid JSON data')
