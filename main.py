from api import run_async, request


def my_task(num: int):
    print(f'Task {num}: started')
    resp = yield request('https://google.com')
    print(f'Task {num}: completed')
    return resp


TASKS = [
    my_task(i) for i in range(50)
]

results = run_async(*TASKS)
print(results)
