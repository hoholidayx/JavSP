# -*- coding: utf-8 -*-
"""
脚本功能说明：
1. 递归遍历指定目录A及其所有子目录，查找所有命名为"poster"的图片文件
2. 将找到的图片扁平复制到目录B（不保留子目录结构），自动处理文件名重复问题
3. 支持分次运行：先执行A→B的复制，再执行C→A的覆盖（需先运行其他脚本处理B目录图片到C目录）
4. 通过JSON映射文件记录原始路径与B/C目录文件名的对应关系，实现精准覆盖

使用步骤：
1. 修改脚本中的DIR_A/DIR_B/DIR_C为实际路径
2. 运行脚本，选择"1"执行A→B的复制（生成映射文件）
3. 运行其他处理脚本，将B目录的图片处理后输出到C目录（保持文件名不变）
4. 再次运行脚本，选择"2"执行C→A的覆盖（读取映射文件，将C目录图片覆盖回A目录原位置）

作者：编程助手
日期：2026-01-30
"""

import os  # 用于文件路径操作、目录遍历
import shutil  # 用于文件复制操作
import json  # 用于读写映射文件
from pathlib import Path  # 用于便捷的目录创建

# ===================== 全局配置 =====================
# 映射文件名称，用于保存原始路径与B/C目录文件名的对应关系
# 该文件是分次运行的核心，执行C→A前请勿删除/修改
MAPPING_FILE = "poster_mapping.json"
TARGET_FILE_NAME = "poster"
# TARGET_FILE_NAME = "disc"

# ===================== 核心函数 =====================
def get_unique_filename(dst_dir: str, filename: str) -> str:
    """
    生成目标目录下不重复的文件名，解决扁平复制时的文件名冲突问题
    规则：若文件已存在，自动在文件名后加数字序号（如 poster.jpg → poster_1.jpg）

    :param dst_dir: 目标目录路径（如 DIR_B）
    :param filename: 原始文件名（如 poster.jpg）
    :return: 目标目录下唯一的文件名（字符串）
    """
    # 拆分文件名和后缀（如 "poster", ".jpg"）
    name, ext = os.path.splitext(filename)
    # 初始化计数器和新文件名
    counter = 1
    new_filename = filename

    # 循环检查文件是否存在，直到生成唯一文件名
    while os.path.exists(os.path.join(dst_dir, new_filename)):
        # 生成带序号的新文件名
        new_filename = f"{name}_{counter}{ext}"
        counter += 1

    return new_filename


def copy_a_to_b(dir_a: str, dir_b: str):
    """
    【操作1】递归查找目录A下的所有poster图片，扁平复制到目录B（核心功能）
    1. 递归遍历dir_a及其所有子目录
    2. 筛选文件名严格为"poster"且是图片格式的文件
    3. 扁平复制到dir_b（不保留子目录结构），自动处理文件名重复
    4. 生成映射文件，记录原始路径与B目录文件名的对应关系

    :param dir_a: 源目录A的绝对路径（如 r"E:\test\dir_a"）
    :param dir_b: 目标目录B的绝对路径（如 r"E:\test\dir_b"）
    """
    # 定义支持的图片后缀（可根据实际需求扩展，如添加.tiff/.svg等）
    SUPPORTED_IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    # 初始化映射字典：key=原始文件路径，value=B目录中的唯一文件名
    poster_mapping = {}

    # 确保目标目录B存在，不存在则创建（parents=True支持创建多级目录，exist_ok=True避免已存在时报错）
    Path(dir_b).mkdir(parents=True, exist_ok=True)

    # 打印开始信息，提升用户体验
    print(f"\n========== 开始执行【A→B】复制操作 ==========")
    print(f"源目录A：{dir_a}")
    print(f"目标目录B：{dir_b}")
    print(f"开始递归查找poster图片...\n")

    # os.walk()递归遍历目录：
    # root: 当前遍历的目录路径
    # dirs: 当前目录下的子目录列表
    # files: 当前目录下的文件列表
    for root, dirs, files in os.walk(dir_a):
        # 遍历当前目录下的所有文件
        for file in files:
            # 拆分文件名和后缀（转小写避免大小写问题，如 Poster.JPG → poster.jpg）
            file_name = os.path.splitext(file)[0].lower()
            file_ext = os.path.splitext(file)[1].lower()

            # 筛选条件：文件名严格等于"poster" + 是支持的图片格式
            if file_name == TARGET_FILE_NAME and file_ext in SUPPORTED_IMAGE_EXT:
                # 拼接原始文件的完整路径
                src_abs_path = os.path.join(root, file)
                # 生成B目录下的唯一文件名（解决重复问题）
                unique_filename = get_unique_filename(dir_b, file)
                # 拼接B目录下的目标路径
                dst_abs_path = os.path.join(dir_b, unique_filename)

                try:
                    # 复制文件：shutil.copy2 保留文件元数据（创建时间、修改时间等），比copy更友好
                    shutil.copy2(src_abs_path, dst_abs_path)
                    # 记录映射关系
                    poster_mapping[src_abs_path] = unique_filename
                    # 打印成功日志，方便追踪
                    print(f"✅ 复制成功：{src_abs_path} → {dst_abs_path}")
                except Exception as e:
                    # 捕获所有异常（如权限不足、文件被占用等），避免脚本崩溃
                    print(f"❌ 复制失败：{src_abs_path} → 原因：{str(e)}")

    # 处理映射文件：只有找到图片时才生成
    if poster_mapping:
        # 写入JSON文件：ensure_ascii=False支持中文路径，indent=4格式化输出（方便查看）
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(poster_mapping, f, ensure_ascii=False, indent=4)

        # 打印统计信息
        mapping_file_abs = os.path.abspath(MAPPING_FILE)
        print(f"\n========== 【A→B】复制操作完成 ==========")
        print(f"📄 映射文件已保存：{mapping_file_abs}")
        print(f"📊 共找到并复制 {len(poster_mapping)} 张poster图片")
    else:
        # 未找到图片时的提示
        print(f"\n========== 【A→B】复制操作完成 ==========")
        print(f"⚠️  未在目录A及其子目录中找到任何poster图片")


def copy_c_to_a(dir_c: str):
    """
    【操作2】读取映射文件，将目录C中处理后的图片覆盖回目录A的原始位置（核心功能）
    1. 检查映射文件是否存在（必须先执行操作1生成）
    2. 读取映射关系，遍历所有原始路径
    3. 查找C目录下对应的处理后图片，覆盖回A目录原位置
    4. 统计成功/失败数量，输出详细日志

    :param dir_c: 处理后图片目录C的绝对路径（如 r"E:\test\dir_c"）
    """
    # 第一步：检查映射文件是否存在
    if not os.path.exists(MAPPING_FILE):
        print(f"\n❌ 错误：未找到映射文件 {MAPPING_FILE}")
        print(f"⚠️  请先执行【操作1】（A→B复制）生成映射文件后，再执行此操作")
        return

    # 第二步：读取映射文件
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            poster_mapping = json.load(f)
    except json.JSONDecodeError:
        print(f"\n❌ 错误：映射文件 {MAPPING_FILE} 格式损坏，无法解析")
        return
    except Exception as e:
        print(f"\n❌ 错误：读取映射文件失败 → 原因：{str(e)}")
        return

    # 第三步：开始覆盖操作
    print(f"\n========== 开始执行【C→A】覆盖操作 ==========")
    print(f"处理后目录C：{dir_c}")
    print(f"映射文件：{os.path.abspath(MAPPING_FILE)}")
    print(f"开始覆盖图片到原始位置...\n")

    # 初始化统计计数器
    success_count = 0  # 覆盖成功数量
    fail_count = 0  # 覆盖失败/跳过数量

    # 遍历映射关系：原始路径 → B/C目录文件名
    for original_abs_path, target_filename in poster_mapping.items():
        # 拼接C目录下处理后图片的完整路径
        processed_abs_path = os.path.join(dir_c, target_filename)

        # 检查处理后图片是否存在
        if not os.path.exists(processed_abs_path):
            print(f"⚠️  跳过：处理后的图片不存在 → {processed_abs_path}")
            fail_count += 1
            continue

        try:
            # 覆盖原始文件：shutil.copy2 保留元数据，覆盖模式（无需额外判断）
            shutil.copy2(processed_abs_path, original_abs_path)
            print(f"✅ 覆盖成功：{processed_abs_path} → {original_abs_path}")
            success_count += 1
        except Exception as e:
            # 捕获异常（如原始文件被占用、权限不足等）
            print(f"❌ 覆盖失败：{processed_abs_path} → 原因：{str(e)}")
            fail_count += 1

    # 打印统计结果
    print(f"\n========== 【C→A】覆盖操作完成 ==========")
    print(f"📊 统计结果：成功 {success_count} 张 | 失败/跳过 {fail_count} 张")


# ===================== 主程序入口 =====================
if __name__ == "__main__":
    """
    主程序逻辑：
    1. 配置路径（用户需修改）
    2. 提供交互式选择，执行对应操作
    """
    # ========== 用户配置区（请根据实际情况修改） ==========
    # 注意：Windows路径建议用r"路径"避免转义，Linux/Mac直接写路径（如 "/home/test/dir_a"）
    DIR_A = r"/Users/hoholiday/Downloads/outputs"  # 源目录A：存放原始poster图片的根目录
    DIR_B = r"/Users/hoholiday/Downloads/input_posters"  # 目标目录B：扁平存放复制后的poster图片
    DIR_C = r"/Users/hoholiday/Downloads/output_posters"  # 处理后目录C：存放其他脚本处理后的图片
    # ====================================================

    # 打印欢迎信息和操作说明
    print("=" * 60)
    print("          Poster图片批量处理脚本（分次运行版）          ")
    print("=" * 60)
    print("操作说明：")
    print("  1. 先执行【操作1】：将A目录的poster图片扁平复制到B目录（生成映射文件）")
    print("  2. 运行其他脚本：处理B目录的图片，输出到C目录（保持文件名不变）")
    print("  3. 再执行【操作2】：将C目录的图片覆盖回A目录原位置")
    print("=" * 60)

    # 交互式选择操作
    while True:
        # 获取用户输入
        choice = input("\n请选择要执行的操作（输入数字1/2，输入q退出）：").strip().lower()

        # 退出逻辑
        if choice == 'q':
            print("👋 脚本已退出")
            break

        # 执行操作1
        elif choice == "1":
            copy_a_to_b(DIR_A, DIR_B)
            break

        # 执行操作2
        elif choice == "2":
            copy_c_to_a(DIR_C)
            break

        # 输入错误处理
        else:
            print("⚠️  输入无效，请输入 1、2 或 q（退出）")