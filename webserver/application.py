from bottle import run, request, Bottle, response, abort, HTTPResponse, app

from webserver.task.TaskController import TaskController
from webserver.user.UserController import UserController


@app.route('/api/start_task', method=['GET'])
def start_task():
    return taskController.start_task(request.params)


@app.route('/api/get_task_logs', method=['GET'])
def get_task_logs():
    return taskController.get_task_logs(request.params)


@app.route('/api/get_task_list', method=['GET'])
def get_task_list():
    return taskController.get_task_list(request.params)


@app.route('/api/list_movie_dir', method=['GET'])
def list_movie_dir():
    return taskController.list_movie_dir(request.params)


@app.route('/api/remove_task', method=['GET'])
def remove_task():
    return taskController.remove_task(request.params)


@app.route('/api/clear_all_tasks', method=['GET', 'POST'])
def clear_all_tasks():
    return taskController.clear_all_tasks(request.params)


@app.route('/login', method=['GET', 'POST', 'OPTIONS'])
def login():
    return userController.login(request, response)


@app.route('/<path:path>', method='OPTIONS')
def handle_options(path):
    """
    处理浏览器预检请求，避免405错误‌
    """
    return HTTPResponse(status=204)


def before_request():
    check_login()


def after_request():
    response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']  # 或指定域名
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, token, Token'
    response.headers['Access-Control-Allow-Credentials'] = 'true'  # 需携带cookie时


def check_login():
    # 排除登录相关路由
    if request.path in ["/login"]:
        return True

    if not userController.check_login(request):
        abort(401, "未登录")


if __name__ == '__main__':
    taskController = TaskController()
    userController = UserController()
    app = Bottle()
    app.config['json.enable'] = True
    app.add_hook("before_request", before_request)
    app.add_hook("after_request", after_request)
    run(app=app, host='localhost', port=7788)
