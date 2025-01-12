class ResponseData(dict):
    STATUS_CODES = {
        0: '成功',
        1: '失败',
        # ... 其他状态码
    }

    def __init__(self, code=0, msg='', data: dict = None):
        super().__init__(data or {})  # 初始化字典部分
        self.code = code
        self.msg = msg or self.STATUS_CODES.get(code, '未知错误')

    def __getattr__(self, item):
        # 获取属性时，优先从字典中获取，否则从自身属性中获取
        try:
            return self[item]
        except KeyError:
            return self.__getattribute__(item)

    def __setattr__(self, key, value):
        # 设置属性时，优先设置到字典中
        if key in self:
            self[key] = value
        else:
            super().__setattr__(key, value)
