import os
import shutil
from pathlib import Path


def merge_folders(source_dir: str, target_dir: str, overwrite: bool = True):
    """
    将源文件夹（A）的所有文件和子文件夹合并到目标文件夹（B）

    Args:
        source_dir: 源文件夹路径（A）
        target_dir: 目标文件夹路径（B）
        overwrite: 是否覆盖目标文件夹中已存在的同名文件，默认True

    Raises:
        FileNotFoundError: 源文件夹不存在时抛出
        PermissionError: 无权限访问文件/文件夹时抛出
    """
    # 转换为Path对象，方便路径操作
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve()

    # 检查源文件夹是否存在
    if not source_path.exists():
        raise FileNotFoundError(f"源文件夹不存在: {source_path}")
    if not source_path.is_dir():
        raise NotADirectoryError(f"指定路径不是文件夹: {source_path}")

    # 遍历源文件夹中的所有文件和子文件夹
    for item in source_path.rglob("*"):
        # 计算当前项相对于源文件夹的相对路径
        relative_path = item.relative_to(source_path)
        # 构建目标路径
        target_item = target_path / relative_path

        try:
            if item.is_file():
                # 处理文件：创建父文件夹，然后复制文件
                target_item.parent.mkdir(parents=True, exist_ok=True)

                # 判断是否覆盖
                if target_item.exists() and not overwrite:
                    print(f"跳过已存在文件（未覆盖）: {target_item}")
                    continue

                # 复制文件（支持大文件，比shutil.copy更稳定）
                shutil.copy2(item, target_item)
                print(f"已复制文件: {item} -> {target_item}")

            elif item.is_dir():
                # 处理文件夹：创建空文件夹（即使源文件夹为空）
                target_item.mkdir(parents=True, exist_ok=True)
                print(f"已创建文件夹: {target_item}")

        except PermissionError as e:
            print(f"权限不足，跳过: {item} | 错误: {e}")
        except Exception as e:
            print(f"处理失败: {item} | 错误: {e}")


def main():
    # ===================== 配置区 =====================
    # 请修改这里的源路径（A）和目标路径（B）
    SOURCE_FOLDER = r"/Users/hoholiday/Downloads/zhengli"  # 源文件夹A
    TARGET_FOLDER = r"/Volumes/A-2/DataBucket/NSFW/movies/演员"  # 目标文件夹B
    OVERWRITE_FILES = True  # 是否覆盖同名文件
    # ==================================================

    print(f"开始合并文件夹：")
    print(f"源文件夹: {SOURCE_FOLDER}")
    print(f"目标文件夹: {TARGET_FOLDER}")
    print(f"覆盖已存在文件: {OVERWRITE_FILES}")
    print("-" * 50)

    try:
        merge_folders(SOURCE_FOLDER, TARGET_FOLDER, OVERWRITE_FILES)
        print("-" * 50)
        print("文件夹合并完成！")
    except Exception as e:
        print(f"合并失败: {e}")


if __name__ == "__main__":
    main()