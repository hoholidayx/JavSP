import json

from webserver.ResponseData import ResponseData
from webserver.task.TaskService import TaskService


class TaskController:

    def __init__(self):
        self._taskService = TaskService()

    def start_task(self, json_data: dict):
        movie_dvdid_list = list()
        if json_data and 'movie_dvdid' in json_data:
            for movie_dvdid in json_data['movie_dvdid']:
                movie_dvdid_list.append(movie_dvdid)
            return ResponseData(data={'movie_num_upper': movie_dvdid_list})
        else:
            return ResponseData(code=1, msg='Invalid JSON data')
