import json
from pprint import pprint
from types import SimpleNamespace
import argparse
import re

def get_obj_dict(obj):
    return obj.__dict__

def get_price(name):
    t = re.search('\((.*?)руб', name)
    return t.group(1)

def run(args):
    data = json.load(open(args.input_file), object_hook=lambda d: SimpleNamespace(**d))

    deps = {}
    for t in data.dependencies.rows:
        if t.to not in deps:
            deps[t.to] = []
        
        deps[t.to].append(t.fromEvent)
    # pprint(deps)

    tasks = []
    for row in data.tasks.rows:
        for child in row.children:
            for t in child.children:
                if t.id in deps:
                    tasks.append((t.id, t.effort, t.name, deps[t.id]))
                else:
                    tasks.append((t.id, t.effort, t.name, []))
    pprint(tasks)

    skill_mapping = {'Тестировщик': 'Тестирование', 
                     'Разработчик': 'Разработка',
                     'Аналитик': 'Аналитика'}
    # pprint(skill_mapping)

    resources = []
    for t in data.resources.rows:
        resources.append((t.id, get_price(t.name), [skill_mapping[t.projectRole]]))

    pprint(resources)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=get_obj_dict, ensure_ascii=False, indent=4)

# ./main.py -i "./inputs/исх.json" -o out.json
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sber Tech Scheduler')
    parser.add_argument('-i', '--input-file', type=str,
                        help='input file', required=True)
    parser.add_argument('-o', '--output-file', type=str,
                        help='output file', required=True)

    args = parser.parse_args()
    run(args)