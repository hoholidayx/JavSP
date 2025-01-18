from bottle import run, request, Bottle

from webserver.task.TaskController import TaskController

app = Bottle()
taskController = TaskController()


@app.route('/api/start_task', method=['POST'])
def start_task():
    return taskController.start_task(request.json)


if __name__ == '__main__':
    app.config['json.enable'] = True
    run(app=app, host='localhost', port=7788)
