import json
from pprint import pprint
from types import SimpleNamespace
import argparse
import re
import xmltodict, json
from datetime import datetime
from libs.examples.solution_printer import SolutionPrinter
from libs.examples.solution_builder import SolutionBuilder
from libs.model.task_scheduling import MinDurationModel, MinCostModel, MinResourcesModel

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
    data = json.load(open(args.input_file), object_hook=lambda d: SimpleNamespace(**d))

    tasks = []
    for t in data.Project.Tasks.Task:
        if t.Summary == "1":
            continue
        if not hasattr(t, 'PredecessorLink'):
            tasks.append((t.UID, t.Name, t.Work, []))
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
                     'Аналитик': 'Аналитика'}
    # pprint(skill_mapping)

    resources = []
    for r in data.Project.Resources.Resource:
        if get_role(r) not in skill_mapping:
            continue
        resources.append((r.UID, get_price(r.Name), [skill_mapping[get_role(r)]]))

    pprint(resources)

    fixed_assignments = []

    model = MinDurationModel(resources, algo_tasks, fixed_assignments)
    # model = MinCostModel(resources, algo_tasks, fixed_assignments)
    # model = MinResourcesModel(resources, algo_tasks, fixed_assignments)
    solution = model.solve()

    print(solution)

    printer = SolutionPrinter()
    print('\nTask assignments:')
    printer.print_task_assignments(tasks, resources, solution['task_assignments'])
    print('\n=============================\n'
        'Resources assignments:')
    printer.print_workers_tasks(tasks, resources, solution['workers_assignments'])


    builder = SolutionBuilder()
    builder.reassign(data, tasks, resources, solution['task_assignments'])
   

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=get_obj_dict, ensure_ascii=False, indent=4)

    with open(args.output_file[:-5] + '.xml', 'w', encoding='utf-8') as f:
        xml_content = xmltodict.unparse(json.load(open(args.output_file)), pretty=True)
        f.write(xml_content)

def convert_xml_to_json(args):
    with open(args.input_file) as fd:
        doc = xmltodict.parse(fd.read())

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=4)

# python main.py -i "./inputs/new/исходные данные.xml" -o "./inputs/new/исходные данные.json" -c 1
# python main.py -i "./inputs/new/исходные данные.json" -o out.json

# python main.py -i "./inputs/v2/тестовое задание.xml" -o "./inputs/v2/тестовое данные.json" -c 1
# python main.py -i "./inputs/v2/тестовое данные.json" -o out2.json
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sber Tech Scheduler')
    parser.add_argument('-i', '--input-file', type=str,
                        help='input file', required=True)
    parser.add_argument('-o', '--output-file', type=str,
                        help='output file', required=True)
    parser.add_argument("-c", '--convert-xml', required=False)

    args = parser.parse_args()
    
    if args.convert_xml is not None:
        pprint("convert xml")
        convert_xml_to_json(args)
    else:
        pprint("process json")
        process_json(args)