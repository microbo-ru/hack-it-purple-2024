import json
from pprint import pprint
from types import SimpleNamespace

import xmltodict

from libs.examples.solution_builder import SolutionBuilder
from libs.examples.solution_printer import SolutionPrinter
from libs.model.solver_params import SolverParams
from libs.model.task_scheduling import MinCostModel
from libs.model.task_scheduling_multiopt import TaskSchedulingMultiOpt
from libs.model.task_scheduling_multiopt_weights import TaskSchedulingMultiOptWeights
from main import INPUT_JSON, find_uid_index, get_effort, clear_task_name, get_price, get_role, OUTPUT_JSON, get_obj_dict




INPUT_JSON = 'in.json'
OUTPUT_JSON = 'out.json'
xml_file = 'C:\\Projects\\hack-it-purple-2024\\inputs\\final\\проверочное задание.xml'
xml_file_out = 'C:\\Projects\\hack-it-purple-2024\\inputs\\final\\проверочное задание out.xml'

with open(xml_file, encoding="utf-8") as fd:
    doc = xmltodict.parse(fd.read())

with open(INPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(doc, f, ensure_ascii=False, indent=4)

# weights = {
#     'duration': 0.1,
#     'cost': 0.8,
#     'resources': 0.1,
# }
# model = TaskSchedulingMultiOptWeights(resources, tasks, weights)
#
# solution = model.solve()
#
# printer = SolutionPrinter()
#
# print('\nTask assignments:\n')
# printer.print_task_assignments(tasks, resources, solution['task_assignments'])
#
# print('\nWork assignments:\n')
# printer.print_workers_tasks(tasks, resources, solution['workers_assignments'])

data = json.load(open(INPUT_JSON, encoding='utf-8'), object_hook=lambda d: SimpleNamespace(**d))

def get_task_skill(t_skill):
    skills = ['Тестирование', 'Разработка', 'Аналитика']

    if t_skill not in skills:
        return ''
    else:
        return t_skill

tasks = []
for t in data.Project.Tasks.Task:
    if t.Summary == "1" or "Веха" in t.Name:
        continue
    if not hasattr(t, 'PredecessorLink'):
        tasks.append((t.UID, t.Name, t.Work, []))
    else:
        if not hasattr(t, 'Work'):
            tasks.append((t.UID, t.Name, "No0H", []))
        else:
            tasks.append((t.UID, t.Name, t.Work, [t.PredecessorLink.PredecessorUID]))
# pprint(tasks)

algo_tasks = []
for t in tasks:
    (uid, name, effort_str, deps) = t
    deps_idx = [find_uid_index(deps[0] , tasks)] if len(deps)> 0 else []
    algo_tasks.append((uid, get_effort(effort_str), get_task_skill(clear_task_name(name)), deps_idx))
pprint(algo_tasks)

skill_mapping = {'Тестировщик': 'Тестирование',
                 'Разработчик': 'Разработка',
                 'Аналитик': 'Аналитика',
                #  'Разработчик': 'Общая', #todo
                #  'Тестировщик': 'Задача', #todo
                 }
# pprint(skill_mapping)

resources = []
for r in data.Project.Resources.Resource:
    if get_role(r) not in skill_mapping:
        continue
    resources.append((r.UID, get_price(r.Name), [skill_mapping[get_role(r)]]))

pprint(resources)

model = MinCostModel(resources, algo_tasks)
solution = model.solve()

printer = SolutionPrinter()
print('\nTask assignments:')
printer.print_task_assignments(tasks, resources, solution['task_assignments'])
print('\n=============================\n'
    'Resources assignments:')
printer.print_workers_tasks(tasks, resources, solution['workers_assignments'])

builder = SolutionBuilder()
builder.reassign(data, tasks, resources, solution['task_assignments'])
builder.update_parents_dates(data)

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(data, f, default=get_obj_dict, ensure_ascii=False, indent=4)

with open(xml_file_out, 'w', encoding='utf-8') as f:
    xml_content = xmltodict.unparse(json.load(open(OUTPUT_JSON, encoding='utf-8')), pretty=True)
    f.write(xml_content)

