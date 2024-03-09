from libs.model.resources.resource_assignment import MinCost

# just for comments
skills = [
    'Analysis',
    'Development',
    'Testing'
]

# name, duration_hrs, skill_required
tasks = [
    ('Requirements Analysis', 10, 0),
    ('API Programming', 20, 1),
    ('API Testing', 5, 2)
]

# name, cost_hr, skill
resources = [
    ('Analyst 1', 50.0, 0),
    ('Analyst 2', 55.0, 0),
    ('Dev', 60.0, 1),
    ('SA', 80.0, 1),
    ('QA1', 40.0, 2),
    ('QA2', 40.0, 2),
]

model = MinCost(resources, tasks)

model.solve()