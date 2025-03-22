from webserver.user.UserService import UserService, SESSION_EXPIRE
from webserver.utils.ResponseData import ResponseData


class UserController:

    def __init__(self):
        self.user_service = UserService()

    def login(self, http_request, http_resp):
        # 获取请求参数
        username = http_request.params.get("username")
        password = http_request.params.get("password")

        result = self.user_service.login(username, password)

        if not result:
            return ResponseData(code=ResponseData.STATUS_CODES_FAILED)

        # 设置客户端 cookie
        http_resp.set_cookie("Auth-Token",
                             result["token"],
                             path="/",  # 全站有效
                             max_age=SESSION_EXPIRE,
                             httponly=False)

        return ResponseData(data=result)

    def check_login(self, request):
        # 检查访问令牌
        token = request.headers.get("Auth-Token") or \
                request.query.get("Auth-Token") or \
                request.get_cookie("Auth-Token")

        return self.user_service.check_login(token)
