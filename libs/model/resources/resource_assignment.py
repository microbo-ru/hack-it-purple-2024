
from ortools.sat.python import cp_model

class MinCost():
    def __init__(self,
                 resources: list,
                 tasks: list):

        self.resources = resources
        self.tasks = tasks

        self.num_workers = len(resources)
        self.num_tasks = len(tasks)


    def solve(self):
        model = cp_model.CpModel()

        # Variables space
        task_workers = {}

        # Potentially every worker can do any task:
        for t in range(self.num_tasks):
            (*_, t_skill) = self.tasks[t]

            for w in range(self.num_workers):
                (*_, w_skill) = self.resources[w]

                if t_skill == w_skill:
                    task_workers[t, w] = model.NewBoolVar(f'task{t}_worker{w}')
                else:
                    task_workers[t, w] = model.NewConstant(False)

        # Constraints:
        # 1. Task is assigned to exactly one worker
        for t in range(self.num_tasks):
            model.AddExactlyOne(task_workers[t, w] for w in range(self.num_workers))

        # Objective function
        obj_task_costs = {}
        for t in range(self.num_tasks):
            (_, task_duration_hrs, _) = self.tasks[t]

            assigned_workers_cost = []
            for w in range(self.num_workers):
                (_, worker_cost_hr, _) = self.resources[w]
                assigned_workers_cost.append(task_workers[t, w] * worker_cost_hr * task_duration_hrs)

            obj_task_costs[t] = sum(assigned_workers_cost)

        model.minimize(sum([obj_task_costs[t] for t in range(self.num_tasks)]))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Total cost = {solver.objective_value}\n')

            for t in range(self.num_tasks):
                for w in range(self.num_workers):
                    if solver.boolean_value(task_workers[t, w]):
                        print(
                            f'Task {t} is performed by worker {w}, cost = {solver.Value(obj_task_costs[t])}'
                        )
        else:
            print("No solution found.")
