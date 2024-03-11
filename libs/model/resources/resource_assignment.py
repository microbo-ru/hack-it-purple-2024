from collections import defaultdict

from ortools.sat.python import cp_model


class MinCost():
    def __init__(self,
                 resources: list,
                 fixed_tasks: list,
                 fixed_assignments: list = []):

        self.resources = resources
        self.fixed_tasks = fixed_tasks
        self.fixed_assignments = fixed_assignments

        self.num_workers = len(resources)
        self.num_tasks = len(fixed_tasks)

        max_day = 0
        for (*_, task_end) in fixed_tasks:
            if task_end > max_day:
                max_day = task_end

        self.num_days = max_day + 1  # zero-based

    def solve(self):
        model = cp_model.CpModel()
        __FALSE = model.NewConstant(False)

        # Variables space:
        # task_workers [d, t, w] -> days x tasks x workers == on what day D what worker W is assigned on task T
        # task_workers = {}
        task_workers = defaultdict(lambda: __FALSE)
        # use default dict with None assignment to speed up iterations over tasks

        # Workers can do tasks based on their skills
        for t in range(self.num_tasks):
            (*_, t_skill, t_start, t_end) = self.fixed_tasks[t]

            for d in range(t_start, t_end + 1):  # +1 - if the day end is the same as day start
                for w in range(self.num_workers):
                    (*_, w_skill) = self.resources[w]

                    # by default = False
                    if t_skill in w_skill:
                        task_workers[d, t, w] = model.NewBoolVar(f'task{t}_worker{w}')

        # Constraints:
        # 0. Fixed assignments should be met
        for (t, w_preferred) in self.fixed_assignments:
            (*_, t_start, t_end) = self.fixed_tasks[t]
            task_workdays = [task_workers[d, t, w_preferred] for d in range(t_start, t_end + 1)]
            model.AddBoolAnd(task_workdays)

        # 1. Task is assigned to exactly one worker
        for t in range(self.num_tasks):
            (*_, t_start, t_end) = self.fixed_tasks[t]

            # 1.1. For every day only 1 worker is assigned
            for d in range(t_start, t_end + 1):
                model.AddExactlyOne(task_workers[d, t, w] for w in range(self.num_workers))

            # 1.2. If worker assigned on 1st day -> he should be assigned on the rest days as well
            # otherwise could be, the task will be performed by different workers on different days
            for w in range(self.num_workers):
                model.AddBoolAnd(task_workers[d, t, w] for d in range(t_start, t_end + 1))\
                     .OnlyEnforceIf(task_workers[t_start, t, w])

                model.AddBoolAnd(task_workers[d, t, w].Not() for d in range(t_start, t_end + 1))\
                     .OnlyEnforceIf(task_workers[t_start, t, w].Not())

        # 2. Worker can do at most 1 task per day
        for w in range(self.num_workers):
            for d in range(self.num_days):
                model.AddAtMostOne(task_workers[d, t, w] for t in range(self.num_tasks))


        # Objective function
        obj_task_costs = {}
        for t in range(self.num_tasks):
            (_, task_effort_hrs, _, t_start, t_end) = self.fixed_tasks[t]

            assigned_workers_cost = []
            for w in range(self.num_workers):
                (_, worker_cost_hr, _) = self.resources[w]
                # to simplify:
                # just consider, if W works on t_start -> consider he is working the whole time as well
                assigned_workers_cost.append(task_workers[t_start, t, w] * worker_cost_hr * task_effort_hrs)

            obj_task_costs[t] = sum(assigned_workers_cost)

        model.minimize(sum([obj_task_costs[t] for t in range(self.num_tasks)]))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Total cost = {solver.objective_value}\n')

            solution = {
                'task_assignments': {},
                'workers_assignments': {}
            }

            for t in range(self.num_tasks):
                (*_, t_start, t_end) = self.fixed_tasks[t]
                for w in range(self.num_workers):
                    if solver.boolean_value(task_workers[t_start, t, w]):
                        # (worker_id, total_cost)
                        solution['task_assignments'][t] = (t_start, t_end, w, solver.Value(obj_task_costs[t]))

            for w in range(self.num_workers):
                worker_solution = []
                for d in range(self.num_days):
                    for t in range(self.num_tasks):
                        if solver.boolean_value(task_workers[d, t, w]):
                            worker_solution.append((d, t))

                solution['workers_assignments'][w] = worker_solution

            return solution

        else:
            print("No solution found.")
            return None
