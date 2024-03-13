
from datetime import datetime, timedelta

class SolutionBuilder:
    def reassign(self, data, tasks, resources, solution_task_assignments):
        date_format = "%Y-%m-%dT%H:%M:%S"
        project_start_date = datetime.strptime(data.Project.StartDate, date_format)

        for t in range(len(tasks)):
            (start, finish, w) = solution_task_assignments[t]
            (task_name, *_) = tasks[t]
            (worker_name, *_) = resources[w]

            # print(f'Task {task_name} is performed by {worker_name} start {start} end {finish}')

            assignment = next(t for t in data.Project.Assignments.Assignment if t.TaskUID == task_name)
            assignment.ResourceUID = worker_name
            new_start = project_start_date + timedelta(days = start)
            new_finish = project_start_date + timedelta(days = finish)
            assignment.Start = new_start.strftime(date_format)
            assignment.Finish = new_finish.strftime(date_format)


            task = next(t for t in data.Project.Tasks.Task if t.UID == task_name)
            new_start = project_start_date + timedelta(days = start)
            new_finish = project_start_date + timedelta(days = finish)
            task.Start = new_start.strftime(date_format)
            task.Finish = new_finish.strftime(date_format)

