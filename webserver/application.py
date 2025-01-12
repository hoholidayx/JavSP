from bottle import run, request, Bottle

from webserver.task.TaskController import TaskController

taskController = TaskController()


def start_task():
    return taskController.start_task(request.json)


if __name__ == '__main__':
    app = Bottle()
    app.route(path='/api/start_task', method='POST', callback=start_task)
    app.config['json.enable'] = True
    run(app=app, host='localhost', port=7788)
