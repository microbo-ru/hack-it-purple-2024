from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar, CpModel

from libs.model.solver_params import SolverParams
from libs.model.task_scheduling import TaskSchedulingBase, MinCostModel, MinResourcesModel, MinDurationModel, \
    max_duration
from libs.model.task_scheduling_multiopt import OptimizationMode


class TaskSchedulingMultiOptWeights(MinCostModel, MinResourcesModel, MinDurationModel):

    opt_mode: list[OptimizationMode]

    def __init__(self,
                 resources: list,                   # (name, cost_hr, skills)
                 tasks: list,                       # (name, effort_hrs, skill_required, depends_on_tasks)
                 opt_weights: {},                   # OptimizationMode -> weight
                 fixed_assignments: list = [],      # (task_id, resource_id)
                 resource_constraints: list = [],   # (resource_id, start, end)
                 task_constraints: list = [],       # (task_id, start, end)
                 solver_params: SolverParams = SolverParams.default()
                 ):

        TaskSchedulingBase.__init__(self, resources, tasks, fixed_assignments, resource_constraints, task_constraints, solver_params)

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

        if not opt_weights:
            raise ValueError("opt_weights should contain at least 1 OptimizationMode")

        self.opt_weights = opt_weights
        self.current_solver = None

    # weighted sum
    # def get_objective(self, model):
    #     objs = []
    #
    #     # if some optimizations were done previously,
    #     # -> lets try to target them
    #     for opt in self.opt_weights:
    #         weight = self.opt_weights[opt]
    #         cls = self.get_cls(opt)
    #         obj_fn = cls.get_objective(self, model)
    #
    #         objs.append((obj_fn, weight))
    #
    #     # weighted sum
    #     weighted_obj = sum([o*w for (o,w) in objs])
    #
    #     return weighted_obj


    def get_objective(self, model):

        if self.current_solver is not None:
            # return 'current' objective
            solver_obj = self.current_solver.get_objective(self, model)
            return solver_obj

        deltas = []

        for opt in self.opt_weights:
            weight = self.opt_weights[opt]
            opt_objective = self.get_cls(opt).get_objective(self, model)
            max_delta = int(self.__maxes[opt] - self.__targets[opt])

            delta = model.NewIntVar(0, max_delta, f'delta_{opt}')
            model.Add(opt_objective >= int(self.__targets[opt]) - delta)
            model.Add(opt_objective <= int(self.__targets[opt]) + delta)

            deltas.append((delta, weight))

        return sum([delta*weight for (delta, weight) in deltas])


    def solve(self):

        solution = None
        self.current_solver = None

        self.__targets = {}
        self.__maxes = {
            'duration': 0,
            'resources': 0,
            'cost': 0
        }

        # optimizations to use:
        for opt in self.opt_weights:
            # print(opt)
            self.current_solver = self.get_cls(opt)
            # call parent class optimization
            solution = self.current_solver.solve(self)

            # objective values
            self.__targets[opt] = solution['objective_value']

            if ('duration' not in self.__maxes) or (solution['duration'] > self.__maxes['duration']):
                self.__maxes['duration'] = solution['duration']

            if ('cost' not in self.__maxes) or (solution['cost'] > self.__maxes['cost']):
                self.__maxes['cost'] = solution['cost']

            if ('resources' not in self.__maxes) or (solution['resources'] > self.__maxes['resources']):
                self.__maxes['resources'] = solution['resources']

        self.current_solver = None
        return TaskSchedulingBase.solve(self)

    def get_cls(self, opt_mode: OptimizationMode):
        match opt_mode:
            case OptimizationMode.DURATION: return MinDurationModel
            case OptimizationMode.COST: return MinCostModel
            case OptimizationMode.RESOURCES: return MinResourcesModel

