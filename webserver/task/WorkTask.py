import os
import traceback
import uuid
from enum import Enum

from javsp.__main__ import RunNormalMode
from javsp.file import scan_movies
from javsp.func import get_scan_dir
from webserver.bridge.bridge import load_config, load_actress_alias_map, import_crawlers, generate_stub_video_files
from webserver.task.Logs import Logs


class WorkTaskState(Enum):
    INIT = 0
    RUNNING = 1
    FINISH_FAILED = 2
    FINISH_SUCCESS = 3


class WorkTask:

    def __init__(self, movie_id: str):
        self.state = WorkTaskState.INIT
        self.id = uuid.uuid4().__str__()
        self.logs = Logs()
        self.movie_ids = list()
        self.movie_ids.append(movie_id)
        """
        任务执行完后回填，与 Movie 相关的结果
        """
        self.task_result = {}

    def to_simple_dict(self):
        return {
            "state": self.state.value,
            "task_id": self.id,
            "movie_ids": self.movie_ids,
        }

    def remove_all_stub_movies(self, movie_list):
        for movie in movie_list:
            if movie.is_stub:
                for file in movie.files:
                    os.remove(file)

    def fill_task_result(self, movies):
        for movie in movies:
            self.task_result[movie.dvdid] = {
                "save_dir": movie.save_dir
            }

    def start(self):
        recognized = list()
        try:
            self.state = WorkTaskState.RUNNING  # Update state on error
            cfg = load_config()
            self.logs.log("Loaded configuration successful")
            actress_alias_map = load_actress_alias_map(cfg)
            self.logs.log("Loaded actress alias map")
            input_dir = get_scan_dir(cfg.scanner.input_directory)
            if input_dir is None:
                raise FileNotFoundError(f"获取输入路径失败：{input_dir}")
            # 创建 Stub Movie 文件
            generate_stub_video_files(self.movie_ids, input_dir)
            # 导入抓取器，必须在chdir之前
            import_crawlers(self.logs)
            os.chdir(input_dir)

            self.logs.log(f'扫描影片文件...')
            recognized = scan_movies(input_dir)
            movie_count = len(recognized)
            if movie_count == 0:
                raise Exception('未找到影片文件')
            # 标记为stub类型
            stub_movies_count = 0
            for movie in recognized:
                if movie.dvdid.casefold() in [x.casefold() for x in self.movie_ids]:
                    movie.is_stub = True
                    stub_movies_count += 1
            self.logs.log(f'扫描影片文件：共找到 {movie_count} 部影片, 其中 {stub_movies_count} 部为占位文件')
            RunNormalMode(cfg, recognized, actress_alias_map, self.logs)
            self.fill_task_result(recognized)
            self.state = WorkTaskState.FINISH_SUCCESS  # Update state on error
        except Exception as e:
            self.state = WorkTaskState.FINISH_FAILED  # Update state on error
            self.logs.log(e.__str__())
            self.logs.log(f"Error occurred: {traceback.format_exc()}")
        finally:
            # 清空所有 stub 类型文件
            for movie in recognized:
                if movie.is_stub:
                    for file_path in movie.files:
                        os.remove(file_path)


if __name__ == '__main__':
    task = WorkTask("midv-999")
    task.start()
