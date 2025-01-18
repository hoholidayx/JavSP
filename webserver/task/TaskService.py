from webserver.task.WorkTask import WorkTask


class TaskService:
    def __init__(self):
        self._tasks = {}

    def start_task(self, movie_id: str):
        task = WorkTask(movie_id)
        task.start()
        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> WorkTask:
        """根据任务 ID 获取任务

        Args:
            task_id (uuid.UUID): 任务 ID

        Returns:
            WorkTask: 找到的任务，如果不存在则返回 None
        """
        return self._tasks.get(task_id)

    def remove_task(self, task_id) -> WorkTask:
        """Remove a task by its ID."""
        return self._tasks.pop(task_id, None)

    def get_all_tasks(self):
        """Get a list of all tasks."""
        return list(self._tasks.values())

    def get_tasks_by_state(self, state) -> []:
        """Get a list of tasks with a specific state."""
        return [task for task in self._tasks.values() if task.state == state]
