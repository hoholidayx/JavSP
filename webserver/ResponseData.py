class ResponseData:
    STATUS_CODES = {
        0: '成功',
        1: '失败',
        # ... 其他状态码
    }

    def __init__(self, code=0, msg='', id: str = None, data: dict = None):
        self.code = code
        self.msg = msg or self.STATUS_CODES.get(code, '未知错误')
        self.id = id
        self.data = data

    def to_dict(self):
        return self.__dict__
