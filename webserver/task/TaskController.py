from webserver.task.TaskService import TaskService


class TaskController:

    def __init__(self):
        self._taskService = TaskService()

    def start_task(self):
        return self._taskService
