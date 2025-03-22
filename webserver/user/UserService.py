# 配置信息
import time
import uuid

from webserver.Configuration import CONFIG

SESSION_EXPIRE = 3600  # 登录有效期1小时（秒）

# 内存存储结构
sessions = {}  # 存储登录会话 {token: {username: str, login_time: float}}


class UserService:

    def __init__(self):
        self.ACCOUNTS = {CONFIG['user']['username']: CONFIG['user']['password_template']}

    def login(self, username, password):
        if username not in self.ACCOUNTS:
            return None
        pwd = self.ACCOUNTS[username]
        # 1. 获取当前日期字符串
        current_date = time.strftime("%Y%m%d")  # 格式示例：20250316

        # 2. 拼接用户输入密码与日期
        combined_password = f"{pwd}{current_date}"

        # 3. 比对预存密码
        success = combined_password == password
        if not success:
            return None

        # 创建会话
        token = str(uuid.uuid4())
        sessions[token] = {
            "username": username,
            "login_time": time.time()
        }

        # 检查历史会话
        for s in sessions:
            self.check_login(s)

        return {
            "token": token,
            "expire_in": SESSION_EXPIRE
        }

    def check_login(self, token):
        if not token or token not in sessions:
            # "未登录或登录已过期"
            return False
        # 检查会话有效期
        session_data = sessions[token]
        if time.time() - session_data["login_time"] > SESSION_EXPIRE:
            sessions.pop(token)
            # "登录已过期"
            return False
        return True
