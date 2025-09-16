import re
from collections import defaultdict

def group_by_result(data):
    # Inicializamos con Corruptible e Incorruptible en 0
    result = {
        'Corruptible': {'count': 0, 'checks': defaultdict(int)},
        'Incorruptible': {'count': 0, 'checks': defaultdict(int)}
    }

    for item in data:
        result_name = item['Result']
        type_name = item['Type']

        if result_name not in result:
            result[result_name] = {'count': 0, 'checks': defaultdict(int)}

        result[result_name]['count'] += 1
        result[result_name]['checks'][type_name] += 1

    # Convertimos defaultdict a dict
    for result_name in result:
        result[result_name]['checks'] = dict(result[result_name]['checks'])

    return result

def parse_type_and_result(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    case_pattern = re.compile(
        r'Type\s*:\s*(.*?)\n'
        r'Result\s*:\s*(.*?)\n',
        re.DOTALL
    )

    matches = case_pattern.findall(content)

    parsed_data = [{"Type": match[0].strip(), "Result": match[1].strip()} for match in matches]

    return parsed_data

def count_result_occurrences(parsed_data):

    result_counts = {
        "Corruptible": 0,
        "Incorruptible": 0,
        "Inconclusive": 0
    }

    for case in parsed_data:
        result = case["Result"]
        if result in result_counts:
            result_counts[result] += 1

    return result_counts