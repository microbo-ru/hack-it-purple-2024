
class SolutionPrinter:

    def print_task_assignments(self, tasks, resources, solution_task_assignments, compact=False):
        __free = u' □'
        __busy = u' ■'

        def get_num_days(solution_task_assignments):
            num_days = 0
            for k, v in solution_task_assignments.items():
                (start, end, w) = v
                if end > num_days:
                    num_days = end

            return num_days

        # find max calendar duration first
        num_days = get_num_days(solution_task_assignments)

        for t in range(len(tasks)):
            (start, end, w) = solution_task_assignments[t]
            (task_name, *_) = tasks[t]
            (worker_name, *_) = resources[w]

            if compact:
                print(f'Task "{task_name}" is performed by "{worker_name}"')

            if not compact:
                day_icons = [__free for _ in range(num_days)]  # empty row
                for d in range(start, end):
                    day_icons[d] = __busy

                day_print = ''.join(day_icons)
                task_print = '{:<5}'.format(task_name)

                print(f'{task_print} : {day_print} : {worker_name}')


    def print_workers_tasks(self, tasks, resources, solution_workers_assignments, compact=False):
        __free = u' □'

        def get_icon(index):
            __icon = [
                u' ♥',
                u' ♦',
                u' ♣',
                u' ♠',
                u' ▲',
                u' ▼',
                u' ©',
                u' *',
                u' 0',
                u' 1',
                u' 2',
                u' 3',
                u' 4',
                u' 5',
                u' 6',
                u' 7',
                u' 8',
                u' 9',
            ]

            return __icon[index % len(__icon)]

        def get_num_days(solution_workers_assignments):
            num_days = 0
            for k, v in solution_workers_assignments.items():
                for (day, task) in v:
                    if day > num_days:
                        num_days = day

            return num_days

        # find max calendar duration first
        num_days = get_num_days(solution_workers_assignments)

        if compact:
            for w in range(len(resources)):
                (worker_name, *_) = resources[w]

                day_tasks = solution_workers_assignments[w]
                print(f'Worker "{worker_name}" is assigned following tasks: {day_tasks}')

        if not compact:
            for w in range(len(resources)):
                (worker_name, *_) = resources[w]

                day_icons = [__free for _ in range(num_days+1)]  # empty row
                for (d, t) in solution_workers_assignments[w]:
                    day_icons[d] = get_icon(t)

                day_print = ''.join(day_icons)
                worker_print = '{:<5}'.format(worker_name)

                print(f'{worker_print} : {day_print}')

            print('\n--- Legend ---')
            for t in range(len(tasks)):
                (task_name, *_) = tasks[t]
                print(f'{get_icon(t)}: {task_name}')
