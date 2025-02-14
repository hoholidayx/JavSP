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
    FINISHED = 2


class WorkTask:

    def __init__(self, movie_id: str):
        self.state = WorkTaskState.INIT
        self.id = uuid.uuid4().__str__()
        self.logs = Logs()
        self.movie_ids = list()
        self.movie_ids.append(movie_id)

    def start(self):
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
                if movie.dvdid in self.movie_ids:
                    movie.is_stub = True
                    stub_movies_count += 1
            self.logs.log(f'扫描影片文件：共找到 {movie_count} 部影片, 其中 {stub_movies_count} 部为占位文件')
            RunNormalMode(cfg, recognized, actress_alias_map, self.logs)
            self.state = WorkTaskState.FINISHED  # Update state on error
        except Exception as e:
            self.state = WorkTaskState.FINISHED  # Update state on error
            self.logs.log(e.__str__())
            self.logs.log(f"Error occurred: {traceback.format_exc()}")


if __name__ == '__main__':
    task = WorkTask("midv-999")
    task.start()
