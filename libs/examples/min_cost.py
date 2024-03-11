from libs.examples.solution_printer import SolutionPrinter
from libs.model.resources.resource_assignment import MinCost

NUM_DAYS = 14

# (name, effort_hrs, skill_required, start_day, end_day)
fixed_tasks = [
    ('Requirements Analysis', 6, 'analysis', 0, 0),
    ('API design', 8, 'dev', 0, 0),
    ('API Programming', 24, 'dev', 1, 4),
    ('DB design', 8, 'dev', 1, 1),
    ('unit-tests', 8, 'dev', 5, 5),
    ('API Testing', 5, 'qa', 5, 5)
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

model = MinCost(resources, fixed_tasks)

solution = model.solve()
# solution = {
#   'task_assignments': {},
#   'workers_assignments': {}
# }


printer = SolutionPrinter(num_days=NUM_DAYS)

print('\nTask assignments:\n')
printer.print_task_assignments(fixed_tasks, resources, solution['task_assignments'])

print('\nWork assignments:\n')
printer.print_workers_tasks(fixed_tasks, resources, solution['workers_assignments'])

