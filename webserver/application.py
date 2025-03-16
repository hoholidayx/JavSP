from bottle import run, request, Bottle, response, abort

from webserver.task.TaskController import TaskController
from webserver.user.UserController import UserController

app = Bottle()
taskController = TaskController()
userController = UserController()


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


@app.route('/login', method=['POST'])
def login():
    return userController.login(request, response)


def before_request():
    REQUEST_METHOD = request.environ.get('REQUEST_METHOD')

    HTTP_ACCESS_CONTROL_REQUEST_METHOD = request.environ.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD')
    if REQUEST_METHOD == 'OPTIONS' and HTTP_ACCESS_CONTROL_REQUEST_METHOD:
        request.environ['REQUEST_METHOD'] = HTTP_ACCESS_CONTROL_REQUEST_METHOD


def after_request():
    response.headers['Access-Control-Allow-Origin'] = '*'
    # response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'


def check_login():
    # 排除登录相关路由
    if request.path in ["/login"]:
        return True

    if not userController.check_login(request):
        abort(400, "未登录")


if __name__ == '__main__':
    app.config['json.enable'] = True
    app.add_hook("before_request", before_request)
    app.add_hook("before_request", check_login)
    app.add_hook("after_request", after_request)
    run(app=app, host='localhost', port=7788)
