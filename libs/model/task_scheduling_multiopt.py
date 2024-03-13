from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar, CpModel

from libs.model.solver_params import SolverParams
from libs.model.task_scheduling import TaskSchedulingBase, MinCostModel, MinResourcesModel, MinDurationModel, \
    max_duration


class OptimizationMode(str, Enum):
    DURATION = 'duration'
    COST = 'cost'
    RESOURCES = 'resources'


class TaskSchedulingMultiOpt(MinCostModel, MinResourcesModel, MinDurationModel):

    opt_mode: list[OptimizationMode]

    def __init__(self,
                 resources: list,                   # (name, cost_hr, skills)
                 tasks: list,                       # (name, effort_hrs, skill_required, depends_on_tasks)
                 opt_mode: list[OptimizationMode],  # list ot optimization priorities
                 fixed_assignments: list = [],      # (task_id, resource_id)
                 solver_params: SolverParams = SolverParams.default()
                 ):

        TaskSchedulingBase.__init__(self, resources, tasks, fixed_assignments, solver_params)

        # self.task_day_workers = None  # task_day_workers[t, d, w] -> tasks x days x workers
        # self.task_workers = None  # task_workers[t, w] -> tasks x workers
        #
        # self.resources = resources
        # self.tasks = tasks
        # self.fixed_assignments = fixed_assignments
        #
        # self.num_workers = len(resources)
        # self.num_tasks = len(tasks)
        #
        # self.num_days = max_duration(tasks)

        if not opt_mode:
            raise ValueError("opt_mode should contain at least 1 OptimizationMode")

        self.opt_mode = opt_mode
        self.current_solver = None
        self.__hints = {}
        self.__accumulated_objs = []


    def get_objective(self, model):

        # if some optimizations were done previously,
        # -> lets try to target them
        for (opt, target) in self.__accumulated_objs:
            cls = self.get_cls(opt)
            obj_fn = cls.get_objective(self, model)
            model.Add(obj_fn == int(target))

        # return 'current' objective
        solver_obj = self.current_solver.get_objective(self, model)
        return solver_obj

    def preprocess_model(self, model: CpModel):
        if not self.__hints:
            pass

        # hints = {
        #     'task_intervals': {},
        #     'task_workers': {},
        #     'task_day_workers': {}
        # }

        if 'task_intervals' in self.__hints:
            for t in range(self.num_tasks):
                (start, end, duration) = self.__hints['task_intervals'][t]
                model.AddHint(self.task_intervals[t].StartExpr(), start)

        if 'task_workers' in self.__hints:
            for t in range(self.num_tasks):
                for w in range(self.num_workers):
                    works = self.__hints['task_workers'][t, w]
                    model.AddHint(self.task_workers[t, w], works)

        if 'task_day_workers' in self.__hints:
            for w in range(self.num_workers):
                for d in range(self.num_days):
                    for t in range(self.num_tasks):
                        works = self.__hints['task_day_workers'][t, d, w]
                        model.AddHint(self.task_day_workers[t, d, w], works)

    def get_cls(self, opt_mode: OptimizationMode):
        match opt_mode:
            case OptimizationMode.DURATION: return MinDurationModel
            case OptimizationMode.COST: return MinCostModel
            case OptimizationMode.RESOURCES: return MinResourcesModel

    def solve(self):

        solution = None
        self.__accumulated_objs = []

        # optimizations to use:
        for opt in self.opt_mode:
            # print(opt)
            self.current_solver = self.get_cls(opt)
            # call parent class optimization
            solution = self.current_solver.solve(self)
            self.__hints = solution['__hints']
            self.__accumulated_objs.append((opt, solution['objective_value']))

        return solution


