import json
import os

from javsp.config import Cfg
from javsp.lib import resource_path
from webserver.task.Logs import Logs


def load_config():
    return Cfg()


def load_actress_alias_map(cfg: Cfg):
    actress_alias_map = None
    if cfg.crawler.normalize_actress_name:
        actress_alias_file_path = resource_path("data/actress_alias.json")
        with open(actress_alias_file_path, "r", encoding="utf-8") as file:
            actress_alias_map = json.load(file)
    return actress_alias_map


def import_crawlers(logs: Logs):
    """按配置文件的抓取器顺序将该字段转换为抓取器的函数列表"""
    unknown_mods = []
    for _, mods in Cfg().crawler.selection.items():
        valid_mods = []
        for name in mods:
            try:
                # 导入fc2fan抓取器的前提: 配置了fc2fan的本地路径
                # if name == 'fc2fan' and (not os.path.isdir(Cfg().Crawler.fc2fan_local_path)):
                #     logger.debug('由于未配置有效的fc2fan路径，已跳过该抓取器')
                #     continue
                import_name = 'javsp.web.' + name
                __import__(import_name)
                valid_mods.append(import_name)  # 抓取器有效: 使用完整模块路径，便于程序实际使用
                logs.log('已配置的抓取器: ' + ', '.join(valid_mods))
            except ModuleNotFoundError:
                unknown_mods.append(name)  # 抓取器无效: 仅使用模块名，便于显示
    if unknown_mods:
        logs.log('配置的抓取器无效: ' + ', '.join(unknown_mods))


def generate_stub_video_files(id_list, filepath_str: str):
    """

        Generate stub video files for each ID in the provided list.

        This function creates dummy MP4 video files of a specified size (1KB) for each ID in the `id_list`.
        The files are saved in the directory specified by `filepath_str`. If the directory does not exist,
        a FileNotFoundError is raised.

        Args:
            id_list (List[str]): A list of IDs used to name the generated video files.
            filepath_str (str): The path to the directory where the video files will be saved.

        Example Usage (not included in actual docstring):
        ```python
        # Assuming you have a list of IDs and a valid directory path
        ids = ["video1", "video2", "video3"]
        path = "/path/to/save/videos/"
        generate_stub_video_files(ids, path)
        ```

    """
    try:
        # 尝试创建目录，如果已存在则忽略
        os.makedirs(filepath_str, exist_ok=True)

        file_subfix = "mp4"
        file_size_bytes = 1024

        for file_id in id_list:
            file_name = os.path.join(filepath_str, f"{file_id}.{file_subfix}")
            with open(file_name, 'wb') as f:
                f.write(b'\0' * file_size_bytes)
    except OSError as e:
        print(f"Error creating files: {e}")
