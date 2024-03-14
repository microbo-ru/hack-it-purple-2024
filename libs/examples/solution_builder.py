from datetime import datetime, timedelta
from pprint import pprint
import copy
import uuid

class SolutionBuilder:
    def reassign(self, data, tasks, resources, solution_task_assignments):
        date_format = "%Y-%m-%dT%H:%M:%S"
        project_start_date = datetime.strptime(data.Project.StartDate, date_format)

        for t in range(len(tasks)):
            (start, finish, w) = solution_task_assignments[t]
            (task_name, *_) = tasks[t]
            (worker_name, *_) = resources[w]

            try:
                assignment = next(t for t in data.Project.Assignments.Assignment if t.TaskUID == task_name)
            except:
                assignment = data.Project.Assignments.Assignment[0] #todo first as template
                assignment = copy.copy(assignment)
                data.Project.Assignments.Assignment.append(assignment)
                assignment.UID = str(len(data.Project.Assignments.Assignment))
                assignment.TaskUID = task_name
                assignment.GUID = str(uuid.uuid4())
                assignment.RemainingWork = 'TBD'
                assignment.Work = 'TBD'

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
            

    def update_parents_dates(self, data):
        node_list = []
        for i in data.Project.Tasks.Task:
            node_list.append(i.OutlineNumber)

        leaves_list = []
        for s in node_list:
            if not any([s in r for r in node_list if s != r]):
                leaves_list.append(s)

        parents_list = [t for t in node_list if t not in leaves_list]

        tasks_with_dates = []
        date_format = "%Y-%m-%dT%H:%M:%S"

        for i in leaves_list:
            try:
                task = next(t for t in data.Project.Tasks.Task if t.OutlineNumber == i)
                tasks_with_dates.append((
                    task.OutlineNumber, 
                    datetime.strptime(task.Start, date_format),
                    datetime.strptime(task.Finish, date_format))
                )
            except:
                pass

        for i in parents_list:
            try:
                task = next(t for t in data.Project.Tasks.Task if t.OutlineNumber == i)
                q = task.OutlineNumber
                all_sub_tasks = list(filter(lambda t: t[0].startswith(q), tasks_with_dates))

                min_start = min(all_sub_tasks, key=lambda t: t[1])[1]
                max_start = max(all_sub_tasks, key=lambda t: t[2])[2]

                task.Start = min_start.strftime(date_format)
                task.Finish = max_start.strftime(date_format)
            except:
                pass

