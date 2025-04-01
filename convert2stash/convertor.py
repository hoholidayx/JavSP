import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# ================= 可配置常量 =================
from video_creator import create_slideshow


class Config:
    # 目录结构相关
    ID_SEPARATOR = "#"  # 电影ID分隔符
    ORIGINAL_EXTRAS_DIR = "extrafanart"  # 原始扩展图片目录名
    NEW_DIR_PREFIX = "fanart#"  # 新目录名前缀
    FILE_NAME_TEMPLATE = "{prefix}{movie_id}{sep}{index}{suffix}"  # 文件名模板

    # 文件匹配相关
    FANART_PREFIX = "fanart"  # 主扩展图文件名前缀

    # 日志相关
    LOG_HEADER = f"\n{'*' * 40}\n"
    LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_INDENT = "  "  # 日志缩进单位

    FORCE_GALLERY_FILE = ".forcegallery"


# ================= 核心逻辑 =================
class MovieProcessor:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.processed_count = 0

    def log(self, action, detail="", level=1):
        """分级日志记录器"""
        timestamp = datetime.now().strftime(Config.LOG_TIME_FORMAT)
        indent = Config.LOG_INDENT * level
        print(f"{timestamp} | {indent}{action}: {detail}")

    def process_all(self):
        self.log("开始处理根目录", str(self.root_path), level=0)
        self.processed_count = 0  # 初始化处理计数

        for root_dir, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                # 使用正则表达式匹配方括号内的内容，例如：[MIDV-999] 死ぬほど嫌いなセクハラ上司に弱み握られ出張相部屋NTR
                match = re.search(r'\[(.*?)\]', dir_name)
                if match:
                    # 提取电影ID
                    movie_id = match.group(1)
                    self.log("提取电影ID", movie_id, level=1)
                    self.process_directory(root_dir, dir_name, movie_id)
                    self.processed_count += 1  # 处理计数+1

        self.log(Config.LOG_HEADER + "处理完成",
                 f"共处理 {self.processed_count} 个电影目录",
                 level=0)

    def process_directory(self, root_dir, dir_name, movie_id):
        self.log(Config.LOG_HEADER + "处理目录", dir_name, level=0)

        movie_dir = Path(f'{root_dir}{os.sep}{dir_name}')
        if not movie_dir.is_dir():
            self.log("跳过非目录项", movie_dir, level=1)
            return

        # 处理fanart文件
        self.process_fanarts(root_dir, movie_dir, movie_id)

        # 处理扩展图片目录
        self.process_extrafanart(root_dir, movie_dir, movie_id)

        # 基于 fanart 生成影片
        self.process_movie(root_dir, dir_name, movie_dir, movie_id)

    def process_movie(self, root_dir, dir_name, movie_dir, movie_id):
        # 查找以 id 为前缀的影片名称
        movie_files = list(movie_dir.glob(f"{movie_id}.*"))
        if not movie_files:
            self.log("未发现任何影片文件")
            return

        # 找到重命名后的 fanart 目录
        new_dir_name = f"{Config.NEW_DIR_PREFIX}{movie_id}"
        image_folder = movie_dir / new_dir_name

        temp_video_name = movie_dir / f'{movie_id}_tmp.mp4'
        new_video_name = movie_dir / f'{dir_name}.mp4'

        self.log("发现影片文件", f"共{len(movie_files)}个，基于{image_folder} \n 生成新影片:{new_video_name}", level=1)

        try:
            # 生成影片
            create_slideshow(
                image_folder=image_folder,  # 替换为你的图片文件夹路径
                output_file=temp_video_name,
                duration_per_image=2,  # 每张显示n秒
                fps=1
            )
        except Exception as e:
            self.log("生成影片异常", str(e), level=1)
            return

        # 删除旧影片
        for movie in movie_files:
            os.remove(movie)

        # 重命名生成的影片
        os.rename(temp_video_name, new_video_name)

    def process_fanarts(self, root_dir, movie_dir, movie_id):
        fanart_files = list(movie_dir.glob(f"{Config.FANART_PREFIX}.*"))
        if not fanart_files:
            return

        self.log("发现fanart文件", f"共{len(fanart_files)}个", level=1)

        # 创建目标目录
        target_dir = movie_dir / Config.ORIGINAL_EXTRAS_DIR
        if not target_dir.exists():
            target_dir.mkdir(exist_ok=True)
            self.log("创建目录", str(target_dir.relative_to(movie_dir)), level=2)

        # 移动文件
        for fanart in fanart_files:
            target = target_dir / fanart.name
            shutil.move(str(fanart), str(target))
            self.log("移动文件",
                     f"{fanart.name} → {target.relative_to(movie_dir)}",
                     level=2)

    def process_extrafanart(self, root_dir, movie_dir, movie_id):
        old_dir = movie_dir / Config.ORIGINAL_EXTRAS_DIR
        new_dir_name = f"{Config.NEW_DIR_PREFIX}{movie_id}"
        new_dir = movie_dir / new_dir_name

        if not old_dir.exists():
            self.log("未找到目录", Config.ORIGINAL_EXTRAS_DIR, level=1)
            return

        try:
            # 重命名目录
            old_dir.rename(new_dir)
            self.log("重命名目录",
                     f"{old_dir.name} → {new_dir.name}",
                     level=1)

            # 处理目录内文件
            self.rename_files(root_dir, new_dir, movie_id)

            # 新增：在重命名后的目录创建标记文件
            self.create_force_gallery(new_dir)  # 传入新目录路径

        except Exception as e:
            self.log("操作异常", str(e), level=1)

    def rename_files(self, root_dir, target_dir, movie_id):
        self.log("开始处理内部文件", str(target_dir.relative_to(root_dir)), level=1)

        files = [f for f in target_dir.iterdir() if f.is_file()]

        # 区分 fanart 文件和其他文件
        fanart_files = [f for f in files if f.name.lower().startswith(Config.FANART_PREFIX)]
        other_files = [f for f in files if not f.name.lower().startswith(Config.FANART_PREFIX)]

        # 按修改时间升序排列其他文件
        other_files.sort(key=lambda f: f.stat().st_mtime, reverse=False)

        # 合并 fanart 文件和其他文件
        sorted_files = fanart_files + other_files

        for idx, file_path in enumerate(sorted_files, 1):
            if not file_path.is_file():
                continue

            new_name = Config.FILE_NAME_TEMPLATE.format(
                prefix=Config.NEW_DIR_PREFIX,
                movie_id=movie_id,
                sep=Config.ID_SEPARATOR,
                index=idx,
                suffix=file_path.suffix
            )

            file_path.rename(target_dir / new_name)
            self.log("重命名文件",
                     f"{file_path.name} → {new_name}",
                     level=2)

        self.log("完成文件处理", f"共 {len(sorted_files)} 个文件", level=1)

    def create_force_gallery(self, target_dir):
        """在指定目录创建标记文件"""
        force_file = target_dir / Config.FORCE_GALLERY_FILE
        try:
            if not target_dir.exists():
                self.log("目标目录不存在", str(target_dir), level=2)
                return

            force_file.touch(exist_ok=True)
            self.log("创建标记文件",
                     f"{Config.FORCE_GALLERY_FILE} @ {force_file.parent.name}",
                     level=2)

        except PermissionError as e:
            self.log("权限拒绝", f"{force_file}: {str(e)}", level=2)
        except Exception as e:
            self.log("创建失败", f"{force_file}: {str(e)}", level=2)


if __name__ == "__main__":
    """
    1、移动 fanart 图片到 extrafanart 目录
    2、按模板重命名 extrafanart 下所有图片
    3、重命名 extrafanart 目录
    4、在重命名后的 extrafanart 路径下创建 .forcegallery 文件
    5、基于 fanart 生成占位影片
    6、修改影片名称为ID+片名，与目录命名一致
    """
    processor = MovieProcessor("/Users/hoholiday/Downloads/movies")  # 修改为实际路径
    processor.process_all()
