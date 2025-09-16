"""
Parser for xverify reports.

This module provides functions to parse checks with their types and results,
count occurrences, and group them by results.

It is specifically for Questa X-Check results.
"""
import re
from collections import defaultdict

def group_by_result(data):
    """
    Group all xverify items by their results.

    :param data: List of dictionaries with "Type" and "Result" keys
    :type data: list of dict
    :return: Dictionary with counts and type per result
    :rtype: dict
    """
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

    for result_name, info in result.items():
        info['checks'] = dict(info['checks'])

    return result

def parse_type_and_result(file_path):
    """
    Parse a xverify report file and extract Type and Result information.

    :param file_path: Path to the report file
    :type file_path: str
    :return: List of dictionaries with "Type" and "Result"
    :rtype: list of dict
    """
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
