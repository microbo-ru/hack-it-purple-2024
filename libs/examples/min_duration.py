from libs.examples.solution_printer import SolutionPrinter
from libs.model.duration.min_duration import MinDuration
from libs.model.resources.resource_assignment import MinCost

NUM_DAYS = 14

# (name, effort_hrs, skill_required, depends_on_tasks)
tasks = [
    ('Requirements Analysis', 6, 'analysis', []),
    ('API design', 8, 'dev', [0]),
    ('DB design', 8, 'dev', [0]),
    ('API Programming', 24, 'dev', [1, 2]),
    ('unit-tests', 8, 'dev', [3]),
    ('API Testing', 5, 'qa', [3])
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

fixed_assignments = [
    # (task_id, resource_id)

    # API should be designed by SA
    (1, 3)
]

model = MinDuration(resources, tasks, fixed_assignments)

solution = model.solve()
# solution = {
#   'task_assignments': {},
#   'workers_assignments': {}
# }


printer = SolutionPrinter(num_days=NUM_DAYS)

print('\nTask assignments:')
printer.print_task_assignments(tasks, resources, solution['task_assignments'])

print('\n=============================\n'
      'Resources assignments:')
printer.print_workers_tasks(tasks, resources, solution['workers_assignments'])

