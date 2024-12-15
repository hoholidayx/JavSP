class Logs:
    def __init__(self):
        self.logs = []

    def log(self, message):
        """
        将日志信息添加到列表中

        Args:
            message (str): 要记录的日志信息
        """
        self.logs.append(message)

    def get_logs(self):
        """
        获取所有的日志信息

        Returns:
            list: 包含所有日志信息的列表
        """
        return self.logs
