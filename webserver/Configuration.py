import yaml

global CONFIG

from pathlib import Path

def get_project_root():
    current_path = Path(__file__).resolve()
    while not (current_path / '.git').exists():
        if current_path.parent == current_path:  # 到达系统根目录时终止
            raise FileNotFoundError("未找到项目根目录")
        current_path = current_path.parent
    return current_path


# 打开文件并加载内容
with open(f'{get_project_root()}/webserver.yml', 'r', encoding='utf-8') as file:
    CONFIG = yaml.safe_load(file)
    print(f'Load config:{CONFIG}')
