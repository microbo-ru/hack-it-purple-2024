from abc import ABC, abstractmethod
from collections import defaultdict

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from libs.model.objective_solution_printer_with_limit import ObjectiveSolutionPrinterWithLimit
from libs.model.solver_params import SolverParams


def max_duration(tasks):
    # https://ru.stackoverflow.com/questions/1331510/%D0%9E%D0%B1%D1%8A%D1%8F%D1%81%D0%BD%D0%B8%D1%82%D0%B5-%D0%BA%D0%B0%D0%BA-%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0%D0%B5%D1%82-%D1%8D%D1%82%D0%BE-%D0%BE%D0%BA%D1%80%D1%83%D0%B3%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5-%D1%87%D0%B8%D1%81%D0%BB%D0%B0-%D0%B2-%D0%B1%D0%BE%D0%BB%D1%8C%D1%88%D1%83%D1%8E-%D1%81%D1%82%D0%BE%D1%80%D0%BE%D0%BD%D1%83
    __HRS_PER_DAY = 8
    tot = 0

    for (name, effort_hrs, skill_required, depends_on_tasks) in tasks:
        task_days = int(-1 * effort_hrs // __HRS_PER_DAY * -1)
        tot += task_days

    return tot


class TaskSchedulingBase(ABC):
    __solver_params: SolverParams

    def __init__(self,
                 resources: list,                   # (name, cost_hr, skills)
                 tasks: list,                       # (name, effort_hrs, skill_required, depends_on_tasks)
                 fixed_assignments: list = [],      # (task_id, resource_id)
                 resource_constraints: list = [],   # (resource_id, start, end)
                 task_constraints: list = [],       # (task_id, start, end)
                 solver_params: SolverParams = SolverParams.default()
                 ):

        # Variable space
        self.task_intervals = None      # task_intervals[t] -> IntervalVar
        self.task_day_workers = None    # task_day_workers[t, d, w] -> tasks x days x workers
        self.task_workers = None        # task_workers[t, w] -> tasks x workers

        self.resources = resources
        self.tasks = tasks
        self.fixed_assignments = fixed_assignments
        self.resource_constraints = resource_constraints
        self.task_constraints = task_constraints

        self.num_workers = len(resources)
        self.num_tasks = len(tasks)

        self.num_days = max_duration(tasks)

        self.__solver_params = solver_params

    def get_hints(self, solver):
        hints = {
            'task_intervals': {},
            'task_workers': {},
            'task_day_workers': {}
        }

        for t in range(self.num_tasks):
            start = solver.Value(self.task_intervals[t].StartExpr())
            end = solver.Value(self.task_intervals[t].EndExpr())
            duration = solver.Value(self.task_intervals[t].SizeExpr())
            hints['task_intervals'][t] = (start, end, duration)

        for t in range(self.num_tasks):
            for w in range(self.num_workers):
                works = solver.Value(self.task_workers[t, w])
                hints['task_workers'][t, w] = works

        for w in range(self.num_workers):
            for d in range(self.num_days):
                for t in range(self.num_tasks):
                    works = solver.boolean_value(self.task_day_workers[t, d, w])
                    hints['task_day_workers'][t, d, w] = works

        return hints

    @abstractmethod
    def get_objective(self, model):
        pass

    @abstractmethod
    def preprocess_model(self, model):
        pass

    def build_model(self):
        model = cp_model.CpModel()
        # Variables space:
        self.task_intervals = {}
        task_starts = {}
        task_durations = {}
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
            task_starts[t] = start
            task_durations[t] = t_duration

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

        # 6. Resource constraints - can't work on specific date, e.g. on vacation
        for (resource_id, start, end) in self.resource_constraints:
            works = [self.task_day_workers[t, d, resource_id].Not() for t in range(self.num_tasks) for d in range(start, end+1)]
            model.AddBoolAnd(works)

        # 7. Task constraints - should be done within a specific date ranges
        for (task_id, start, end) in self.task_constraints:
            if start is not None:
                model.Add(task_starts[task_id] >= start)
            if end is not None:
                model.Add((task_starts[task_id] + task_durations[task_id]) <= end)

        return model


    def to_results(self, solver):
        solution = {
            'objective_value': solver.objective_value,
            '__hints': {},
            'task_assignments': {},
            'workers_assignments': {},
            'tot_days': 0,
            'tot_workers': 0,
            'tot_cost': 0
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

        solution['__hints'] = self.get_hints(solver)

        tot_days = 0
        tot_workers = {}
        tot_cost = 0
        for t in solution['task_assignments']:
            (start, end, assigned_worker) = solution['task_assignments'][t]

            if end > tot_days:
                tot_days = end

            tot_workers[assigned_worker] = True

            (_, effort_hrs, _, _) = self.tasks[t]
            (_, cost_hr, _) = self.resources[assigned_worker]
            tot_cost += int(effort_hrs) * int(cost_hr)

        solution['duration'] = tot_days
        solution['cost'] = tot_cost
        solution['resources'] = len(tot_workers)

        return solution

    def setup_solver_params(self, solver):
        if self.__solver_params.max_iteration_search_time:
            solver.parameters.max_time_in_seconds = self.__solver_params.max_iteration_search_time
        if self.__solver_params.num_search_workers:
            solver.num_search_workers = self.__solver_params.num_search_workers
        if self.__solver_params.do_logging:
            solver.parameters.log_search_progress = self.__solver_params.do_logging

    def get_printer(self):
        if self.__solver_params.solution_limit:
            solution_printer = ObjectiveSolutionPrinterWithLimit(self.__solver_params.solution_limit)
        else:
            solution_printer = cp_model.ObjectiveSolutionPrinter()

        return solution_printer

    def solve(self):
        model = self.build_model()
        self.preprocess_model(model)
        model.minimize(self.get_objective(model))

        solver = cp_model.CpSolver()

        self.setup_solver_params(solver)
        solution_printer = self.get_printer()

        print("Solving started...")
        status = solver.Solve(model, solution_printer)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Solution found. Total objective func = {solver.objective_value}\n')
            return self.to_results(solver)
        else:
            print("No solution found.")
            return None


class MinCostModel(TaskSchedulingBase):
    def preprocess_model(self, model):
        pass

    def get_objective(self, model):
        # Objective - Min cost
        obj_task_costs = {}
        for t in range(self.num_tasks):
            (_, effort_hrs, _, _) = self.tasks[t]

            assigned_workers_cost = []
            for w in range(self.num_workers):
                (_, cost_hr, _) = self.resources[w]
                assigned_workers_cost.append(self.task_workers[t, w] * int(effort_hrs) * int(cost_hr))

            obj_task_costs[t] = sum(assigned_workers_cost)

        return sum(obj_task_costs[t] for t in range(self.num_tasks))


class MinResourcesModel(TaskSchedulingBase):
    def preprocess_model(self, model):
        pass

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
    def preprocess_model(self, model):
        pass

    def get_objective(self, model):
        # Objective - Min Duration

        root_end = model.NewIntVar(0, self.num_days, f'root_end')

        for t in range(self.num_tasks):
            task_interval = self.task_intervals[t]
            task_end = task_interval.EndExpr()

            model.Add(task_end <= root_end)

        return root_end
