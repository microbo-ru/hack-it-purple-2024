
class SolutionPrinter:
    def __init__(self, num_days=0):
        self.num_days = num_days

    def print_task_assignments(self, tasks, resources, solution_task_assignments, compact=False):
        __free = u' □ '
        __busy = u' ■ '

        for t in range(len(tasks)):
            (w, cost) = solution_task_assignments[t]
            (task_name, *_, start_day, end_day) = tasks[t]
            (worker_name, *_) = resources[w]

            if compact:
                print(f'Task "{task_name}" is performed by "{worker_name}", cost = {cost}')

            if not compact:
                day_icons = [__free for _ in range(self.num_days)]  # empty row
                for d in range(start_day, end_day + 1):
                    day_icons[d] = __busy

                day_print = ''.join(day_icons)
                task_print = '{:<25}'.format(task_name)

                print(f'{task_print} : {day_print} : {worker_name} ({cost})')

    def print_workers_tasks(self, tasks, resources, solution_workers_assignments, compact=False):
        __free = u' □ '
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

        if compact:
            for w in range(len(resources)):
                (worker_name, *_) = resources[w]

                day_tasks = solution_workers_assignments[w]
                print(f'Worker "{worker_name}" is assigned following tasks: {day_tasks}')

        if not compact:
            for w in range(len(resources)):
                (worker_name, *_) = resources[w]

                day_icons = [__free for _ in range(self.num_days)]  # empty row
                for (d, t) in solution_workers_assignments[w]:
                    day_icons[d] = __icon[t]

                day_print = ''.join(day_icons)
                worker_print = '{:<25}'.format(worker_name)

                print(f'{worker_print}: {day_print}')

            print('\n--- Legend ---')
            for t in range(len(tasks)):
                (task_name, *_) = tasks[t]
                print(f'{__icon[t]}: {task_name}')
