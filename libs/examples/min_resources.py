from libs.examples.solution_printer import SolutionPrinter
from libs.model.task_scheduling import MinResourcesModel

# (name, effort_hrs, skill_required, depends_on)
tasks = [
    ('Requirements Analysis', 6, 'analysis', []),
    ('API design', 8, 'dev', []),
    ('API Programming', 24, 'dev', []),
    ('DB design', 8, 'dev', []),
    ('unit-tests', 8, 'dev', []),
    ('API Testing', 5, 'qa', [])
]

# (name, cost_hr, skills)
resources = [
    ('Analyst 1', 50.0, ['analysis']),
    ('Analyst 2', 55.0, ['analysis']),
    ('Dev', 60.0, ['dev']),
    ('SA', 80.0, ['analysis', 'dev']),
    ('QA1', 40.0, ['qa']),
    ('QA2', 40.0, ['qa']),
]

model = MinResourcesModel(resources, tasks)

solution = model.solve()
# solution = {
#   'task_assignments': {},
#   'workers_assignments': {}
# }


printer = SolutionPrinter()

print('\nTask assignments:\n')
printer.print_task_assignments(tasks, resources, solution['task_assignments'])

print('\nWork assignments:\n')
printer.print_workers_tasks(tasks, resources, solution['workers_assignments'])

