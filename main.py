from pprint import pprint
from types import SimpleNamespace
import argparse
import re
import xmltodict, json
from datetime import datetime
from libs.examples.solution_printer import SolutionPrinter
from libs.examples.solution_builder import SolutionBuilder
from libs.model.task_scheduling_multiopt import TaskSchedulingMultiOpt
from libs.model.solver_params import SolverParams


INPUT_JSON = './tmp/input.json'
OUTPUT_JSON = './tmp/out.json'
RES_DIR = './results'

def get_obj_dict(obj):
    return obj.__dict__

def get_price(name):
    t = re.search('\((.*?)руб', name)
    return int(t.group(1))

def find_uid_index(uid, tasks):
    i=0
    for t in tasks:
        (t_uid, *_) = t
        if t_uid == uid:
            return i
        i+=1
    
    return None

def get_effort(effort_str):
    return int(effort_str[2: effort_str.index('H')])

def get_role(resource):
    return resource.Name[:resource.Name.index(' ')]

def clear_task_name(task_name):
    if ' ' in task_name:
        return task_name[:task_name.index(' ')]
    else:
        return task_name

def process_json(args):
    data = json.load(open(INPUT_JSON), object_hook=lambda d: SimpleNamespace(**d))

    tasks = []
    for t in data.Project.Tasks.Task:
        if t.Summary == "1":
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
        algo_tasks.append((uid, get_effort(effort_str), clear_task_name(name), deps_idx))
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

    s_params = SolverParams.default()
    s_params.max_iteration_search_time = args.max_time
    model = TaskSchedulingMultiOpt(resources, algo_tasks, opt_mode=args.mode_list, solver_params=s_params)
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

    with open(args.output_file, 'w', encoding='utf-8') as f:
        xml_content = xmltodict.unparse(json.load(open(OUTPUT_JSON)), pretty=True)
        f.write(xml_content)

def convert_xml_to_json(args):
    with open(args.input_file) as fd:
        doc = xmltodict.parse(fd.read())

    with open(INPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent = 4)

# export PYTHONPATH=/home/vladimir/Work/microbo/hack-it-purple-2024
# python main.py -i "./inputs/v2/тестовое задание.xml" -o ./results/result_2.xml -m duration
# python main.py -i "./inputs/new/исходные данные.xml" -o ./results/result_1.xml -m duration
# python main.py -i "./inputs/final/проверочное задание.xml" -o ./results/final_duration.xml -m duration
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sber Tech Task Scheduler')
    parser.add_argument('-i', '--input-file', type=str,
                        help='input xml file', required=True)
    parser.add_argument('-o', '--output-file', type=str,
                        help='output xml file', required=True)
    parser.add_argument('-t', '--max-time', type=int, default=600,
                        help='Max iteration search time in seconds')
    parser.add_argument('-m', '--mode-list', nargs='+', type=str, required=True,
                        help='duration, cost, resources')

    args = parser.parse_args()

    convert_xml_to_json(args)
    process_json(args)
