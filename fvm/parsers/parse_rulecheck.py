import re

from collections import defaultdict

def group_by_severity(data):
    result = {
        'Violation': {'count': 0, 'checks': defaultdict(int)},
        'Caution': {'count': 0, 'checks': defaultdict(int)}
    }

    for item in data:
        severity = item['Severity']
        type_name = item['Type']

        if severity not in result:
            result[severity] = {'count': 0, 'checks': defaultdict(int)}

        result[severity]['count'] += 1
        result[severity]['checks'][type_name] += 1

    for severity in result:
        result[severity]['checks'] = dict(result[severity]['checks'])

    return result

def parse_type_and_severity(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    case_pattern = re.compile(
        r'Type\s*:\s*(.*?)\n'
        r'Severity\s*:\s*(.*?)\n',
        re.DOTALL
    )

    matches = case_pattern.findall(content)

    parsed_data = [{"Type": match[0].strip(), "Severity": match[1].strip()} for match in matches]

    return parsed_data

def count_severity_occurrences(parsed_data):

    severity_counts = {
        "Violation": 0,
        "Caution": 0,
        "Inconclusive": 0
    }

    for case in parsed_data:
        severity = case["Severity"]
        if severity in severity_counts:
            severity_counts[severity] += 1

    return severity_counts