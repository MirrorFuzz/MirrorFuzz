import json

from src.utils.utils import list_files

pytorch = list_files('../issues/filter/tensorflow')
count = 0
for i in pytorch:
    with open(i, 'r') as f:
        data = json.load(f)
        for issues in data:
            count +=  len(issues['code'])
print(count)
