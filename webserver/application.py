import json

from bottle import route, run, request

from webserver.ResponseData import ResponseData
from webserver.task.TaskController import TaskController

taskController = TaskController()


@route('/')
def index():
    resp = ResponseData(data={"test": f"Hello, World!{taskController.start_task()}"})
    return resp.to_dict()


@route('/api/start', method='POST')
def process_movie_num():
    data = request.json
    if data and 'movie_num' in data:
        movie_num_upper = data['movie_num'].upper()
        return json.dumps({'movie_num_upper': movie_num_upper})
    else:
        return json.dumps({'error': 'Invalid JSON data'})


if __name__ == '__main__':
    run(host='localhost', port=7788)
