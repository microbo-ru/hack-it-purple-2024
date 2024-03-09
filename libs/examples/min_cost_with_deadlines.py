from libs.examples.solution_printer import SolutionPrinter
from libs.model.task_scheduling import MinCostModel

# (name, effort_hrs, skill_required, depends_on)
tasks = [
    ('Requirements Analysis', 6, 'analysis', []),
    ('API design', 8, 'dev', [0]),
    ('DB design', 8, 'dev', [0]),
    ('API Programming', 24, 'dev', [1, 2]),
    ('Dev 1', 24, 'dev', [1]),
    ('Dev 2', 24, 'dev', [1]),
    ('Dev 3', 24, 'dev', [1]),
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

deadlines = [
    # all dev tasks should be completed by 12th
    (4, None, 12),
    (5, None, 12),
    (6, None, 12)
]

model = MinCostModel(resources, tasks, task_constraints=deadlines)

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

