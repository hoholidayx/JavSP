import subprocess
import os
import argparse
import shutil
import sys
import datetime
import tempfile

# --- Helper Functions ---

def find_7zip_executable():
    """(Copied from previous script) Tries to find the 7-Zip executable."""
    executable_name = '7z.exe' if os.name == 'nt' else '7z'
    path = shutil.which(executable_name)
    if path:
        print(f"找到 7-Zip: {path}")
        return path
    if os.name == 'nt':
        possible_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "7-Zip", "7z.exe"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                print(f"找到 7-Zip: {p}")
                return p
    print("错误: 未能在系统 PATH 或常见安装位置找到 7-Zip 可执行文件。")
    print(f"请确保已安装 7-Zip 并将其添加到 PATH，或使用 --seven_zip_path 参数指定路径。")
    return None

def parse_datetime_string(datetime_str):
    """(Copied from previous script) Parses various datetime string formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
        "%Y%m%d%H%M%S",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    try:
        # Try interpreting as timestamp if formats fail
        ts = float(datetime_str)
        # Basic sanity check for typical timestamp range (e.g., > year 1970)
        if ts > 0:
             return datetime.datetime.fromtimestamp(ts)
        else:
             raise ValueError("时间戳数值无效")
    except ValueError:
        raise ValueError(f"无法解析日期时间字符串: '{datetime_str}'. "
                         f"请尝试 YYYY-MM-DD HH:MM:SS 或类似格式, 或 Unix 时间戳。")


# --- Main Archiving Logic ---

def archive_modified_files_7z(
    source_dir,
    archive_path,
    mod_time_dt,
    seven_zip_path,
    volume_size=None,
    password=None,
    archive_format="7z",
    compression_level=5
    ):
    """
    Scans source_dir for files modified after mod_time_dt, then uses 7-Zip
    to create an archive (optionally split, encrypted) containing only those files,
    preserving directory structure.

    Args:
        source_dir (str): Path to the source directory to scan.
        archive_path (str): Output archive path (full path for single file,
                             base name for split volumes).
        mod_time_dt (datetime.datetime): Threshold modification time.
        seven_zip_path (str): Path to the 7-Zip executable.
        volume_size (str, optional): Volume size for splitting (e.g., '100m'). Defaults to None.
        password (str, optional): Password for encryption. Defaults to None.
        archive_format (str, optional): Archive format ('7z' or 'zip'). Defaults to '7z'.
        compression_level (int, optional): Compression level (0-9). Defaults to 5.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.isdir(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在或不是一个目录。")
        return False

    mod_timestamp_threshold = mod_time_dt.timestamp()
    files_to_archive = [] # List to store relative paths of files to add

    print(f"开始扫描目录: {source_dir}")
    print(f"查找修改时间晚于 {mod_time_dt} 的文件...")

    # Step 1: Find modified files and get their relative paths
    try:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_mod_time = os.path.getmtime(file_path)
                    if file_mod_time > mod_timestamp_threshold:
                        # Get path relative to source_dir for inclusion in archive
                        relative_path = os.path.relpath(file_path, source_dir)
                        files_to_archive.append(relative_path)
                        # print(f"  发现: {relative_path}") # Verbose output if needed
                except FileNotFoundError:
                    print(f"  警告: 文件在扫描期间消失: {file_path}")
                except OSError as e:
                    print(f"  警告: 无法访问文件属性 {file_path}: {e}")
    except Exception as e:
        print(f"扫描目录时出错: {e}")
        return False

    # Step 2: Check if any files were found
    if not files_to_archive:
        print("\n没有找到符合条件的已修改文件。无需创建压缩包。")
        return True # Consider this a success (nothing to do)

    print(f"\n找到 {len(files_to_archive)} 个符合条件的文件。准备创建压缩包...")

    # Step 3: Create a temporary list file
    temp_list_file = None
    temp_list_file_name = ""
    try:
        # Use NamedTemporaryFile to handle temporary file creation and naming
        # delete=False is important because 7z needs to open the file by name *after* we close it.
        # We will manually delete it in the finally block.
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as temp_f:
            temp_list_file_name = temp_f.name
            print(f"创建临时文件列表: {temp_list_file_name}")
            for rel_path in files_to_archive:
                temp_f.write(rel_path + '\n')
        # File is now closed but still exists

        # Step 4: Build the 7-Zip command
        # Ensure output directory exists
        output_dir = os.path.dirname(archive_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                print(f"创建输出目录: {output_dir}")
                os.makedirs(output_dir)
            except OSError as e:
                 print(f"错误: 无法创建输出目录 '{output_dir}': {e}")
                 return False # Return early before cleanup attempt

        command = [
            seven_zip_path,
            'a',                           # Add command
            f'-t{archive_format}',        # Archive type
            f'-mx={compression_level}',   # Compression level
        ]
        if password:
            command.append(f'-p{password}')
            if archive_format.lower() == '7z':
                command.append('-mhe=on')
        if volume_size:
            command.append(f'-v{volume_size}')

        command.append(archive_path) # Output archive path/base
        # Use @listfile syntax to specify files to include
        command.append(f'@{temp_list_file_name}')
        command.append('-y') # Auto-confirm

        print("\n将执行以下 7-Zip 命令:")
        # Quote arguments with spaces for readability, especially the list file path
        print(" ".join(f'"{arg}"' if (" " in arg or arg.startswith('@')) else arg for arg in command))
        # Note: We will run this command with cwd=source_dir
        print(f"(将在工作目录 '{source_dir}' 中执行)")
        print("-" * 30)

        # Step 5: Execute the 7-Zip command
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # *** CRITICAL: Set cwd=source_dir ***
        # This tells 7-Zip that the relative paths in the list file
        # should be interpreted relative to the source directory,
        # thus preserving the structure correctly in the archive.
        result = subprocess.run(
            command,
            check=True,         # Raise error on non-zero exit code
            capture_output=True,# Capture stdout/stderr
            text=True,          # Decode as text
            encoding=sys.stdout.encoding or 'utf-8', # Use console encoding
            cwd=source_dir,     # <<< Run 7z from the source directory
            startupinfo=startupinfo
        )

        print("7-Zip 输出:")
        print(result.stdout)
        print("-" * 30)
        if volume_size:
            print(f"成功创建分卷压缩包，基础名称为: {archive_path}")
        else:
             print(f"成功创建单个压缩文件: {archive_path}")
        return True

    except FileNotFoundError:
        print(f"错误: 无法找到 7-Zip 可执行文件 '{seven_zip_path}'。请检查路径。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: 7-Zip 执行失败，返回码: {e.returncode}")
        print("7-Zip 错误输出:")
        # Decode stderr if possible
        stderr_output = e.stderr
        # try:
        #     stderr_output = e.stderr.decode(sys.stderr.encoding or 'utf-8')
        # except Exception:
        #     stderr_output = str(e.stderr) # Fallback
        print(stderr_output)
        return False
    except Exception as e:
        print(f"处理或执行 7-Zip 时发生意外错误: {e}")
        return False
    finally:
        # Step 6: Cleanup the temporary list file
        if temp_list_file_name and os.path.exists(temp_list_file_name):
            try:
                print(f"删除临时文件列表: {temp_list_file_name}")
                os.remove(temp_list_file_name)
            except OSError as e:
                print(f"警告: 无法删除临时文件 '{temp_list_file_name}': {e}")

# --- Command Line Interface ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="查找指定修改时间之后的文件, 并使用 7-Zip 将这些文件打包 (保持目录结构), 支持分卷和加密。",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Required arguments
    parser.add_argument("source_dir",
                        help="要扫描的源目录路径。")
    parser.add_argument("archive_path",
                        help="输出压缩文件的路径。\n"
                             "- 如果指定了 --volume-size, 此为分卷的基础名 (例如 'my_archive')。\n"
                             "- 如果未指定 --volume-size, 此为完整的压缩文件名 (例如 'my_archive.7z')。")
    parser.add_argument("mod_time",
                        help="修改时间阈值。只打包此时间之后修改的文件。\n"
                             "接受格式如: 'YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DD', Unix 时间戳等。")

    # Optional arguments (for 7-Zip control)
    parser.add_argument("-v", "--volume-size",
                        help="（可选）设置每个分卷的大小 (例如 '100m', '50k', '1g')。\n"
                             "如果省略，则创建单个（非分卷）压缩文件。",
                        default=None)
    parser.add_argument("-p", "--password",
                        help="（可选）设置压缩文件密码进行加密。",
                        default=None)
    parser.add_argument("--seven_zip_path",
                        help="（可选）7-Zip 可执行文件的路径。\n"
                             "如果省略，脚本会尝试自动查找。",
                        default=None)
    parser.add_argument("--format",
                        choices=['7z', 'zip'],
                        default='7z',
                        help="压缩格式 (默认: 7z)。")
    parser.add_argument("--level",
                        type=int,
                        choices=range(10),
                        default=5,
                        metavar='[0-9]',
                        help="压缩级别 (0=存储, 9=极限)。默认: 5")

    args = parser.parse_args()

    # Find 7-Zip executable
    sz_path = args.seven_zip_path
    if not sz_path:
        sz_path = find_7zip_executable()
        if not sz_path:
            sys.exit(1)
    elif not os.path.exists(sz_path) or not os.path.isfile(sz_path):
         print(f"错误: 指定的 7-Zip 路径无效或不是文件: {sz_path}")
         sys.exit(1)

    # Parse modification time
    try:
        modification_time_dt = parse_datetime_string(args.mod_time)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    # Execute the main logic
    success = archive_modified_files_7z(
        source_dir=args.source_dir,
        archive_path=args.archive_path,
        mod_time_dt=modification_time_dt,
        seven_zip_path=sz_path,
        volume_size=args.volume_size,
        password=args.password,
        archive_format=args.format,
        compression_level=args.level
    )

    if success:
        print("\n操作成功完成。")
    else:
        print("\n操作失败。")
        sys.exit(1)