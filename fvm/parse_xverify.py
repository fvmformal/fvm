import re

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