from bottle import run, request, Bottle, response

from webserver.task.TaskController import TaskController

app = Bottle()
taskController = TaskController()


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


@app.route('/api/clear_all_tasks', method=['GET'])
def clear_all_tasks():
    return taskController.clear_all_tasks(request.params)


def before_request():
    REQUEST_METHOD = request.environ.get('REQUEST_METHOD')

    HTTP_ACCESS_CONTROL_REQUEST_METHOD = request.environ.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD')
    if REQUEST_METHOD == 'OPTIONS' and HTTP_ACCESS_CONTROL_REQUEST_METHOD:
        request.environ['REQUEST_METHOD'] = HTTP_ACCESS_CONTROL_REQUEST_METHOD


def after_request():
    response.headers['Access-Control-Allow-Origin'] = '*'
    # response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'


if __name__ == '__main__':
    app.config['json.enable'] = True
    app.add_hook("before_request", before_request)
    app.add_hook("after_request", after_request)
    run(app=app, host='localhost', port=7788)
