from abc import ABC, abstractmethod
from collections import defaultdict

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar


def max_duration(tasks):
    # https://ru.stackoverflow.com/questions/1331510/%D0%9E%D0%B1%D1%8A%D1%8F%D1%81%D0%BD%D0%B8%D1%82%D0%B5-%D0%BA%D0%B0%D0%BA-%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0%D0%B5%D1%82-%D1%8D%D1%82%D0%BE-%D0%BE%D0%BA%D1%80%D1%83%D0%B3%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D1%87%D0%B8%D1%81%D0%BB%D0%B0-%D0%B2-%D0%B1%D0%BE%D0%BB%D1%8C%D1%88%D1%83%D1%8E-%D1%81%D1%82%D0%BE%D1%80%D0%BE%D0%BD%D1%83
    __HRS_PER_DAY = 8
    tot = 0

    for (name, effort_hrs, skill_required, depends_on_tasks) in tasks:
        task_days = int(-1 * effort_hrs // __HRS_PER_DAY * -1)
        tot += task_days

    return tot


class TaskSchedulingBase(ABC):
    def __init__(self,
                 resources: list,                   # (name, cost_hr, skills)
                 tasks: list,                       # (name, effort_hrs, skill_required, depends_on_tasks)
                 fixed_assignments: list = []):     # (task_id, resource_id)

        # Variable space
        self.task_intervals = None      # task_intervals[t] -> IntervalVar
        self.task_day_workers = None    # task_day_workers[t, d, w] -> tasks x days x workers
        self.task_workers = None        # task_workers[t, w] -> tasks x workers

        self.resources = resources
        self.tasks = tasks
        self.fixed_assignments = fixed_assignments

        self.num_workers = len(resources)
        self.num_tasks = len(tasks)

        self.num_days = max_duration(tasks)

    @abstractmethod
    def get_objective(self, model):
        pass

    def build_model(self):
        model = cp_model.CpModel()
        # Variables space:
        self.task_intervals = {}
        # day_overlaps [t, d] -> tasks x days, task is performed on a day
        day_overlaps = {}
        # task_workers [t, w] -> tasks x workers
        self.task_workers = {}
        # task_day_workers [t, d, w] -> tasks x days x workers
        self.task_day_workers = {}
        # 1. Construct variable space
        for t in range(self.num_tasks):
            t_duration = max_duration([self.tasks[t]])

            start = model.NewIntVar(0, self.num_days, f'start_task{t}')
            interval = model.NewFixedSizedIntervalVar(start, t_duration, f'interval_task{t}')
            end = interval.EndExpr()

            self.task_intervals[t] = interval

            for d in range(self.num_days):
                overlap_d = model.NewBoolVar(f'overlap_t{t}_d{d}')
                before_d = model.NewBoolVar(f'before_t{t}_d{d}')
                after_d = model.NewBoolVar(f'after_t{t}_d{d}')

                model.Add(start <= d).OnlyEnforceIf(overlap_d)
                model.Add(end > d).OnlyEnforceIf(overlap_d)  # Intervals are open-ended on the right

                model.Add(end <= d).OnlyEnforceIf(before_d)
                model.Add(start > d).OnlyEnforceIf(after_d)

                model.Add(overlap_d + before_d + after_d == 1)
                day_overlaps[t, d] = overlap_d
        # 2. Add dependencies on intervals
        for t in range(self.num_tasks):
            (*_, depends_on_tasks) = self.tasks[t]

            for dep in depends_on_tasks:
                interval = self.task_intervals[t]  # this interval
                dependency = self.task_intervals[dep]

                model.Add(interval.StartExpr() >= dependency.EndExpr())  # intervals are open-ended
        # 3. Daily constraints
        # 3.0 task x daily x *worker space + task x worker space
        for t in range(self.num_tasks):
            for w in range(self.num_workers):
                self.task_workers[t, w] = model.NewBoolVar(f'task{t}_worker{w}')

                for d in range(self.num_days):
                    self.task_day_workers[t, d, w] = model.NewBoolVar(f'task{t}_day{d}_worker{w}')

                # link dimensions
                days = [self.task_day_workers[t, d, w] for d in range(self.num_days)]
                model.Add(sum(days) > 0).OnlyEnforceIf(self.task_workers[t, w])
                model.Add(sum(days) == 0).OnlyEnforceIf(self.task_workers[t, w].Not())
        # 3.1 Task should be done by a single worker at a day if task is being performed
        #     and by nobody if it is not
        for t in range(self.num_tasks):
            for d in range(self.num_days):
                works = [self.task_day_workers[t, d, w] for w in range(self.num_workers)]

                model.Add(sum(works) == 1).OnlyEnforceIf(day_overlaps[t, d])
                model.Add(sum(works) == 0).OnlyEnforceIf(day_overlaps[t, d].Not())
        # 3.2 Worker can work on a single task at max a day
        for w in range(self.num_workers):
            for d in range(self.num_days):
                tasks = [self.task_day_workers[t, d, w] for t in range(self.num_tasks)]

                model.Add(sum(tasks) <= 1)
        # 3.3 only 1 worker should work on the task
        for t in range(self.num_tasks):
            works = [self.task_workers[t, w] for w in range(self.num_workers)]
            model.AddExactlyOne(works)
        # 4. Skills matching
        for t in range(self.num_tasks):
            (*_, skill_required, _) = self.tasks[t]

            if skill_required is None or skill_required == '':
                continue

            for w in range(self.num_workers):
                (*_, skills) = self.resources[w]
                if skill_required not in skills:
                    model.Add(self.task_workers[t, w] == 0)
        # 5. Fixed assignments should be met
        for (t, w_preferred) in self.fixed_assignments:
            model.Add(self.task_workers[t, w_preferred] == 1)
        return model

    def to_results(self, solver):
        solution = {
            'task_assignments': {},
            'workers_assignments': {}
        }
        for t in range(self.num_tasks):
            start = solver.Value(self.task_intervals[t].StartExpr())
            end = solver.Value(self.task_intervals[t].EndExpr())

            assigned_worker = -1

            for w in range(self.num_workers):
                # first match is the answer
                if solver.Value(self.task_workers[t, w]):
                    assigned_worker = w
                    break

            solution['task_assignments'][t] = (start, end, assigned_worker)
        for w in range(self.num_workers):
            worker_solution = []
            for d in range(self.num_days):
                for t in range(self.num_tasks):
                    if solver.boolean_value(self.task_day_workers[t, d, w]):
                        worker_solution.append((d, t))

            solution['workers_assignments'][w] = worker_solution
        return solution

    def solve(self):
        model = self.build_model()

        model.minimize(self.get_objective(model))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10 * 60
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Solution found. Total objective func = {solver.objective_value}\n')
            return self.to_results(solver)
        else:
            print("No solution found.")
            return None


class MinCostModel(TaskSchedulingBase):
    def get_objective(self, model):
        # Objective - Min cost
        obj_task_costs = {}
        for t in range(self.num_tasks):
            (_, effort_hrs, _, _) = self.tasks[t]

            assigned_workers_cost = []
            for w in range(self.num_workers):
                (_, cost_hr, _) = self.resources[w]
                assigned_workers_cost.append(self.task_workers[t, w] * effort_hrs * cost_hr)

            obj_task_costs[t] = sum(assigned_workers_cost)

        return sum(obj_task_costs[t] for t in range(self.num_tasks))


class MinResourcesModel(TaskSchedulingBase):
    def get_objective(self, model):
        # Objective - Min resources
        obj_task_workers = {}
        for w in range(self.num_workers):
            obj_task_workers[w] = model.NewBoolVar(f'worker{w}_is_used')

            tasks = [self.task_workers[t, w] for t in range(self.num_tasks)]
            model.Add(sum(tasks) > 0).OnlyEnforceIf(obj_task_workers[w])
            model.Add(sum(tasks) == 0).OnlyEnforceIf(obj_task_workers[w].Not())

        return sum(obj_task_workers[w] for w in range(self.num_workers))


class MinDurationModel(TaskSchedulingBase):
    def get_objective(self, model):
        # Objective - Min Duration

        root_end = model.NewIntVar(0, self.num_days, f'root_end')

        for t in range(self.num_tasks):
            task_interval = self.task_intervals[t]
            task_end = task_interval.EndExpr()

            model.Add(task_end <= root_end)

        return root_end
