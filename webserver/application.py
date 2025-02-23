from bottle import run, request, Bottle

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


if __name__ == '__main__':
    app.config['json.enable'] = True
    run(app=app, host='localhost', port=7788)
