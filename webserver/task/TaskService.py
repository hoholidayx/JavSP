import concurrent.futures
import os

from webserver.task.WorkTask import WorkTask


def build_directory_tree_non_recursive(root_dir):
    """
    非递归方式构建表示目录结构的字典。

    Args:
        root_dir: 根目录路径。

    Returns:
        一个字典，表示目录树结构。
    """

    tree = {}
    stack = [(root_dir, tree)]  # 使用栈来模拟递归

    while stack:
        current_dir, current_tree = stack.pop()
        for item in os.listdir(current_dir):
            full_path = os.path.join(current_dir, item)
            if os.path.isfile(full_path):
                current_tree[item] = full_path
            elif os.path.isdir(full_path):
                current_tree[item] = {}  # 创建子目录字典
                stack.append((full_path, current_tree[item]))  # 将子目录添加到栈中

    return tree


class TaskService:
    def __init__(self):
        self._tasks = {}
        self._task_future_map = {}
        self._executor = concurrent.futures.ThreadPoolExecutor()  # 创建线程池

    def start_task(self, movie_id: str):
        task = WorkTask(movie_id)
        # 将 task.start() 方法提交到线程池异步执行
        future = self._executor.submit(task.start)
        self._tasks[task.id] = task
        self._task_future_map[task.id] = future
        return task

    def get_task(self, task_id: str) -> WorkTask | None:
        """根据任务 ID 获取任务

        Args:
            task_id (uuid.UUID): 任务 ID

        Returns:
            WorkTask: 找到的任务，如果不存在则返回 None
        """
        try:
            return self._tasks[task_id]
        except Exception:
            return None

    def remove_task(self, task_id) -> WorkTask | None:
        """Remove a task by its ID."""
        try:
            if task_id in self._task_future_map:
                future = self._task_future_map[task_id]
                if future:
                    future.cancel()
            if task_id in self._tasks:
                return self._tasks.pop(task_id, None)
        except Exception:
            print(f"remove_task 失败，找不到 task_id:{task_id}")
        return None

    def remove_all_tasks(self) -> int:
        """Remove a task by its ID."""
        try:
            for f in self._task_future_map.values():
                if not f.done() or f.running():
                    f.cancel()
            self._task_future_map.clear()
            task_len = self._tasks.__len__()
            self._tasks.clear()
            return task_len
        except Exception:
            return -1

    def get_all_tasks(self):
        """Get a list of all tasks."""
        return list(self._tasks.values())

    def get_tasks_by_state(self, state) -> []:
        """Get a list of tasks with a specific state."""
        return [task for task in self._tasks.values() if task.state == state]

    def list_movie_dir(self, task_id, movie_dvdid) -> dict | None:
        task = self.get_task(task_id)
        if task and (movie_dvdid in task.task_result):
            movie_result = task.task_result[movie_dvdid]
            if not movie_result:
                print(f"无影片结果！{movie_dvdid}")
                return None
            save_dir = movie_result["save_dir"]
            if not save_dir:
                print(f"无影片保存目录！{movie_dvdid}")
                return None
            dir_tree = build_directory_tree_non_recursive(save_dir)
            return dir_tree
        else:
            print(f"找不到对应Task！{movie_dvdid}")
            return None
