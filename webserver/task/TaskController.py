from webserver.ResponseData import ResponseData
from webserver.task.TaskService import TaskService


class TaskController:

    def __init__(self):
        self._taskService = TaskService()

    def start_task(self, query_param: dict):
        movie_dvdid = query_param['movie_dvdid']
        if movie_dvdid:
            task = self._taskService.start_task(movie_dvdid)
            return ResponseData(data={"task_id": task.id})
        else:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED, msg='Invalid JSON data')

    def get_task_logs(self, query_param: dict):
        task_id = query_param['task_id']
        task = self._taskService.get_task(task_id)
        if not task:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED, msg=f"Failed to find task[id:{task_id}]")
        else:
            return ResponseData(data={
                "log_list": task.logs.get_logs(),
                "task": task.to_simple_dict()
            })

    def get_task_list(self, query_param: dict):
        tasks = self._taskService.get_all_tasks()
        response_data = list()
        for task in tasks:
            response_data.append(task.to_simple_dict())
        return ResponseData(data={"task_list": response_data})

    def list_movie_dir(self, query_param):
        movie_dvdid = query_param["movie_dvdid"]
        task_id = query_param["task_id"]
        dir_tree = self._taskService.list_movie_dir(task_id, movie_dvdid)
        if not dir_tree:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED, msg=f"Failed to find task[id:{task_id}]")
        return ResponseData(data={movie_dvdid: dir_tree})

    def remove_task(self, query_param):
        task_id = query_param['task_id']
        task = self._taskService.remove_task(task_id)
        if task:
            return ResponseData(data={"task_id": task_id})
        else:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED)

    def clear_all_tasks(self, query_param):
        task_size = self._taskService.get_all_tasks().__sizeof__()
        self._taskService.remove_all_tasks()
        return ResponseData(data={"task_size": task_size})
