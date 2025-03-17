import re

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