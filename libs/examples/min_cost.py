from libs.model.resources.resource_assignment import MinCost


# just for comments
skills = [
    'Analysis',
    'Development',
    'Testing'
]

NUM_DAYS = 14

# (name, effort_hrs, skill_required, start_day, end_day)
tasks = [
    ('Requirements Analysis', 6, 'analysis', 0, 0),
    ('API Programming', 24, 'dev', 1, 4),
    ('DB design', 8, 'dev', 1, 1),
    ('unit-tests', 8, 'dev', 5, 5),
    ('API Testing', 5, 'qa', 5, 5)
]

# (name, cost_hr, skill)
resources = [
    ('Analyst 1', 50.0, 'analysis'),
    ('Analyst 2', 55.0, 'analysis'),
    ('Dev', 60.0, 'dev'),
    ('SA', 80.0, 'dev'),
    ('QA1', 40.0, 'qa'),
    ('QA2', 40.0, 'qa'),
]

model = MinCost(resources, tasks)

solution = model.solve()
# solution = {
#   'task_assignments': {},
#   'workers_assignments': {}
# }

# print solutions

__free = u' □ '
__busy = u' ■ '
__icon = [
    u' ♥ ',
    u' ♦ ',
    u' ♣ ',
    u' ♠ ',
    u' ▲ ',
    u' ▼ ',
    u' © ',
    u' * '
]

def print_task_assignments(short = False):
    global t, task_name, _, worker_name

    if short:
        for t in range(len(tasks)):
            (worker, cost) = solution['task_assignments'][t]
            (task_name, *_) = tasks[t]
            (worker_name, *_) = resources[worker]

            print(f'Task "{task_name}" is performed by "{worker_name}", cost = {cost}')

    if not short:
        for t in range(len(tasks)):
            (worker, cost) = solution['task_assignments'][t]
            (task_name, *_, start_day, end_day) = tasks[t]
            (worker_name, *_) = resources[worker]

            day_icons = [__free for _ in range(NUM_DAYS)]  # empty row
            for d in range(start_day, end_day + 1):
                day_icons[d] = __busy
            day_print = ''.join(day_icons)

            task_print = '{:<25}'.format(task_name)

            print(f'{task_print} : {day_print} : {worker_name} ({cost})')


def print_worker_tasks(short = False, print_legend = True):
    global worker_name, _, t, task_name

    if short:
        for w in range(len(resources)):
            (worker_name, *_) = resources[w]
            day_tasks = solution['workers_assignments'][w]
            print(f'Worker "{worker_name}" is assigned following tasks: {day_tasks}')

    if not short:
        for w in range(len(resources)):
            (worker_name, *_) = resources[w]

            day_icons = [__free for _ in range(NUM_DAYS)]  # empty row
            for (d, t) in solution['workers_assignments'][w]:
                day_icons[d] = __icon[t]

            day_print = ''.join(day_icons)
            worker_print = '{:<25}'.format(worker_name)

            print(f'{worker_print}: {day_print}')

    if print_legend:
        print('\n--- Legend ---')
        for t in range(len(tasks)):
            (task_name, *_) = tasks[t]
            print(f'{__icon[t]}: {task_name}')


print('\nTask assignments:\n')
print_task_assignments()

print('\nWork assignments:\n')
print_worker_tasks()

