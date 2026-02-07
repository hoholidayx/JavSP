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
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')  # 支持的图片格式
    # 保留的文件前缀（不处理这些文件）
    PRESERVED_FILE_PREFIXES = ("landscape", "disc", "poster")

    # 日志相关
    LOG_HEADER = f"\n{'*' * 40}\n"
    LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_INDENT = "  "  # 日志缩进单位

    FORCE_GALLERY_FILE = ".forcegallery"
    # 是否重命名 extrafanarts 目录
    ENABLE_RENAME_FANARTS_DIR_NAME = False


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

    def is_already_renamed(self, file_path, movie_id):
        """检查文件是否已经按模板重命名过"""
        pattern = re.compile(
            rf"^{re.escape(Config.NEW_DIR_PREFIX)}{re.escape(movie_id)}{re.escape(Config.ID_SEPARATOR)}\d+(\.\w+)$"
        )
        return pattern.match(file_path.name) is not None

    def is_image_file(self, file_path):
        """检查文件是否为图片"""
        return file_path.suffix.lower() in Config.IMAGE_EXTENSIONS

    def is_preserved_file(self, file_path):
        """检查是否为需要保留的文件（landscape/disc/poster）"""
        file_prefix = file_path.name.split('.')[0].lower()
        return file_prefix in Config.PRESERVED_FILE_PREFIXES

    def get_next_available_index(self, target_dir, movie_id):
        """获取下一个可用的文件序号（避免重命名冲突）"""
        existing_files = list(target_dir.glob(f"{Config.NEW_DIR_PREFIX}{movie_id}{Config.ID_SEPARATOR}*"))
        indexes = []
        for file in existing_files:
            match = re.search(rf"{re.escape(Config.ID_SEPARATOR)}(\d+)\.", file.name)
            if match:
                indexes.append(int(match.group(1)))
        return max(indexes) + 1 if indexes else 1

    def process_all(self):
        self.log("开始处理根目录", str(self.root_path), level=0)
        self.processed_count = 0  # 初始化处理计数

        for root_dir, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                # 使用正则表达式匹配方括号内的内容，例如：[MIDV-999] 死ぬほど嫌いなセクハラ上司に弱み握られ出張相部屋NTR
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

        # 新增：将poster图片复制为disc图片
        self.copy_poster_to_disc(movie_dir)

        # 处理fanart文件（复制而非移动）
        self.process_fanarts(root_dir, movie_dir, movie_id)

        # 处理扩展图片目录
        self.process_extrafanart(root_dir, movie_dir, movie_id)

        # 基于 fanart 生成影片
        self.process_movie(root_dir, dir_name, movie_dir, movie_id)

    def copy_poster_to_disc(self, movie_dir):
        """将poster图片复制为disc图片（幂等，已存在则跳过）"""
        self.log("开始处理poster→disc复制", level=1)

        # 查找poster图片文件
        poster_files = [
            f for f in movie_dir.glob("poster.*")
            if self.is_image_file(f)
        ]

        if not poster_files:
            self.log("未找到poster图片文件", level=2)
            return

        # 取第一个poster文件（通常只有一个）
        poster_file = poster_files[0]
        # 构建disc文件名（保持相同后缀）
        disc_file = movie_dir / f"disc{poster_file.suffix}"

        # 检查disc文件是否已存在
        if disc_file.exists():
            self.log("disc图片已存在，跳过复制", f"{disc_file.name}", level=2)
            return

        # 复制文件（保留原poster文件）
        try:
            shutil.copy2(str(poster_file), str(disc_file))
            self.log("复制poster为disc图片", f"{poster_file.name} → {disc_file.name}", level=2)
        except Exception as e:
            self.log("复制poster→disc失败", f"{str(e)}", level=2)

    def process_movie(self, root_dir, dir_name, movie_dir, movie_id):
        # 查找以 id 为前缀的影片名称
        movie_files = [f for f in movie_dir.glob(f"{movie_id}.*") if not f.name.endswith('_tmp.mp4')]
        if not movie_files:
            # 检查是否已经生成过目标影片
            target_movie = movie_dir / f'{dir_name}.mp4'
            if target_movie.exists():
                self.log("已存在目标影片文件", str(target_movie), level=1)
                return
            self.log("未发现任何影片文件", level=1)
            return

        # 找到重命名后的 fanart 目录
        new_dir_name = f"{Config.NEW_DIR_PREFIX}{movie_id}"
        if Config.ENABLE_RENAME_FANARTS_DIR_NAME:
            image_folder = movie_dir / new_dir_name
        else:
            image_folder = movie_dir / Config.ORIGINAL_EXTRAS_DIR

        if not image_folder.exists():
            self.log("图片目录不存在", str(image_folder), level=1)
            return

        temp_video_name = movie_dir / f'{movie_id}_tmp.mp4'
        new_video_name = movie_dir / f'{dir_name}.mp4'

        # 如果临时文件存在，先删除
        if temp_video_name.exists():
            self.log("清理残留临时文件", str(temp_video_name), level=1)
            os.remove(temp_video_name)

        # 如果目标文件已存在，跳过生成
        if new_video_name.exists():
            self.log("目标影片已存在，跳过生成", str(new_video_name), level=1)
            # 删除旧影片文件
            for movie in movie_files:
                if movie != new_video_name:
                    os.remove(movie)
                    self.log("清理旧影片文件", str(movie), level=1)
            return

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
            # 清理临时文件
            if temp_video_name.exists():
                os.remove(temp_video_name)
            return

        # 删除旧影片
        for movie in movie_files:
            try:
                os.remove(movie)
                self.log("删除旧影片", str(movie), level=2)
            except Exception as e:
                self.log("删除旧影片失败", f"{movie}: {str(e)}", level=2)

        # 重命名生成的影片
        if temp_video_name.exists():
            os.rename(temp_video_name, new_video_name)
            self.log("重命名生成的影片", f"{temp_video_name} → {new_video_name}", level=1)
        else:
            self.log("临时影片文件不存在，重命名失败", str(temp_video_name), level=1)

    def process_fanarts(self, root_dir, movie_dir, movie_id):
        # 只匹配图片类型的fanart文件，排除保留文件
        fanart_files = [
            f for f in movie_dir.glob(f"{Config.FANART_PREFIX}.*")
            if self.is_image_file(f) and not self.is_preserved_file(f)
        ]
        if not fanart_files:
            self.log("未发现fanart图片文件", level=1)
            return

        self.log("发现fanart图片文件", f"共{len(fanart_files)}个", level=1)

        # 创建目标目录（强制创建，已存在则忽略）
        target_dir = movie_dir / Config.ORIGINAL_EXTRAS_DIR
        target_dir.mkdir(exist_ok=True)  # 确保目录存在，无论是否已存在
        self.log("确保目标目录存在", str(target_dir.relative_to(movie_dir)), level=2)

        # 复制文件（不再跳过已存在的，强制覆盖/重新生成序号1文件）
        for fanart in fanart_files:
            # 构建目标文件名（按模板重命名，固定序号1）
            target_name = Config.FILE_NAME_TEMPLATE.format(
                prefix=Config.NEW_DIR_PREFIX,
                movie_id=movie_id,
                sep=Config.ID_SEPARATOR,
                index=1,
                suffix=fanart.suffix
            )
            target = target_dir / target_name

            # 强制复制（覆盖已存在的文件）
            try:
                # 复制文件（不覆盖已存在的，但确保执行复制流程）
                if not target.exists():
                    shutil.copy2(str(fanart), str(target))
                    self.log("复制并重命名文件",
                             f"{fanart.name} → {target.relative_to(movie_dir)} (序号固定为1)",
                             level=2)
                else:
                    self.log("序号1文件已存在，跳过复制（但仍执行后续重命名）", f"{target.name}", level=2)
            except Exception as e:
                self.log("复制fanart文件失败", f"{fanart.name}: {str(e)}", level=2)

            # 将原目录的fanart文件重命名为landscape（保持原后缀）
            landscape_file = movie_dir / f"landscape{fanart.suffix}"
            # 强制重命名：如果已存在则先删除旧的landscape文件
            try:
                if landscape_file.exists():
                    os.remove(landscape_file)
                    self.log("删除已存在的landscape文件", landscape_file.name, level=2)
                # 执行重命名
                fanart.rename(landscape_file)
                self.log("重命名原fanart文件为landscape（强制）",
                         f"{fanart.name} → {landscape_file.name}",
                         level=2)
            except Exception as e:
                self.log("重命名fanart为landscape失败", f"{fanart.name}: {str(e)}", level=2)


    def process_extrafanart(self, root_dir, movie_dir, movie_id):
        old_dir = movie_dir / Config.ORIGINAL_EXTRAS_DIR
        if Config.ENABLE_RENAME_FANARTS_DIR_NAME:
            new_dir_name = f"{Config.NEW_DIR_PREFIX}{movie_id}"
        else:
            new_dir_name = Config.ORIGINAL_EXTRAS_DIR

        new_dir = movie_dir / new_dir_name

        if not old_dir.exists():
            # 检查新目录是否已存在
            if new_dir.exists():
                self.log("目标目录已存在，跳过重命名", f"{new_dir.name}", level=1)
                # 仍需处理目录内文件和创建标记文件
                self.rename_files(root_dir, new_dir, movie_id)
                self.create_force_gallery(new_dir)
            else:
                self.log("未找到目录", Config.ORIGINAL_EXTRAS_DIR, level=1)
            return

        try:
            # 检查新目录是否已存在
            if new_dir.exists():
                self.log("目标目录已存在，跳过重命名", f"{new_dir.name}", level=1)
                # 处理原目录文件到新目录
                for file in old_dir.iterdir():
                    if file.is_file() and self.is_image_file(file) and not self.is_preserved_file(file):
                        # 检查目标文件是否已存在（避免重复）
                        target_file = new_dir / file.name
                        if self.is_already_renamed(file, movie_id):
                            # 如果源文件已重命名，直接检查目标是否存在
                            if not target_file.exists():
                                shutil.move(str(file), str(target_file))
                                self.log("迁移已重命名文件", f"{file.name} → {new_dir.name}", level=2)
                        else:
                            # 未重命名文件，先检查是否已有对应序号文件
                            target_name = Config.FILE_NAME_TEMPLATE.format(
                                prefix=Config.NEW_DIR_PREFIX,
                                movie_id=movie_id,
                                sep=Config.ID_SEPARATOR,
                                index=self.get_next_available_index(new_dir, movie_id),
                                suffix=file.suffix
                            )
                            target_file = new_dir / target_name
                            if not target_file.exists():
                                shutil.move(str(file), str(target_file))
                                self.log("迁移并命名文件", f"{file.name} → {target_name}", level=2)
                # 删除空的旧目录
                if not any(old_dir.iterdir()):
                    old_dir.rmdir()
                    self.log("删除空目录", old_dir.name, level=2)
            else:
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

        # 只处理图片文件，排除标记文件和保留文件
        files = [
            f for f in target_dir.iterdir()
            if f.is_file() and self.is_image_file(f)
               and f.name != Config.FORCE_GALLERY_FILE
               and not self.is_preserved_file(f)
        ]

        # 区分已重命名/未重命名的文件
        renamed_files = [f for f in files if self.is_already_renamed(f, movie_id)]
        unrenamed_files = [f for f in files if not self.is_already_renamed(f, movie_id)]

        self.log("文件分类统计", f"已重命名:{len(renamed_files)} | 待重命名:{len(unrenamed_files)}", level=2)

        # 按修改时间升序排列未重命名文件
        unrenamed_files.sort(key=lambda f: f.stat().st_mtime, reverse=False)

        # 获取起始序号（已重命名文件的最大序号 +1，无则从2开始，因为fanart固定为1）
        start_index = self.get_next_available_index(target_dir, movie_id)
        # 确保fanart的序号1优先，如果还没占用则从1开始
        fanart_1_exists = any(self.is_already_renamed(f, movie_id) and "1." in f.name for f in renamed_files)
        if start_index == 1 and not fanart_1_exists:
            start_index = 1
        elif start_index == 1 and fanart_1_exists:
            start_index = 2

        # ========== 核心逻辑：只处理未重命名的文件 ==========
        total_renamed = 0

        # 处理剩余未重命名文件
        for idx, file_path in enumerate(unrenamed_files, start=start_index):
            # 跳过fanart文件（已经在process_fanarts中处理）
            if file_path.name.lower().startswith(Config.FANART_PREFIX):
                continue

            new_name = Config.FILE_NAME_TEMPLATE.format(
                prefix=Config.NEW_DIR_PREFIX,
                movie_id=movie_id,
                sep=Config.ID_SEPARATOR,
                index=idx,
                suffix=file_path.suffix
            )
            new_path = target_dir / new_name

            # 跳过已存在的文件
            if new_path.exists():
                self.log("文件已存在，跳过重命名", f"{file_path.name} → {new_name}", level=2)
                continue

            file_path.rename(new_path)
            self.log("重命名文件",
                     f"{file_path.name} → {new_name}",
                     level=2)
            total_renamed += 1

        self.log("完成文件处理", f"本次重命名 {total_renamed} 个文件 | 目录总文件数 {len(files)}", level=1)

    def create_force_gallery(self, target_dir):
        """在指定目录创建标记文件（幂等）"""
        force_file = target_dir / Config.FORCE_GALLERY_FILE
        try:
            if not target_dir.exists():
                self.log("目标目录不存在", str(target_dir), level=2)
                return

            # 如果文件已存在，跳过创建
            if force_file.exists():
                self.log("标记文件已存在，跳过创建", f"{Config.FORCE_GALLERY_FILE}", level=2)
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
    1、保留 landscape/disc/poster 文件在原目录，不做任何处理
    2、新增：将poster图片复制为disc图片（已存在则跳过）
    3、复制（而非移动）fanart 图片到 extrafanart 目录，并按模板重命名为序号1，同时将原fanart重命名为landscape
    4、按模板重命名 extrafanart 下所有图片（只处理未重命名的图片，跳过已命名的）
    5、重命名 extrafanart（幂等，已存在则迁移文件并清理空目录）
    6、在重命名后的 extrafanart 路径下创建 .forcegallery 文件（已存在则跳过）
    7、基于 fanart 生成占位影片（已存在则跳过生成，只清理旧文件）
    8、修改影片名称为ID+片名，与目录命名一致（幂等，避免重复生成）
    9、强化幂等性，多次执行不会产生重复文件或错误
    """
    processor = MovieProcessor("/Users/hoholiday/Downloads/outputs")  # 修改为实际路径
    processor.process_all()