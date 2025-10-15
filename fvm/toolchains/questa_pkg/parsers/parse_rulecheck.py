"""
Parser for rulecheck reports.

This module provides functions to parse checks with their types and severities,
count occurrences, and group them by severity.

It is specifically for Questa AutoCheck results.
"""
import re

from collections import defaultdict

def group_by_severity(data):
    """
    Group all rulecheck items by their severity.

    :param data: List of dictionaries with "Type" and "Severity" keys
    :type data: list of dict
    :return: Dictionary with counts and type per severity
    :rtype: dict
    """
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

    for severity, info in result.items():
        info['checks'] = dict(info['checks'])

    return result

def parse_type_and_severity(file_path):
    """
    Parse a rulecheck report file and extract Type and Severity information.

    :param file_path: Path to the report file
    :type file_path: str
    :return: List of dictionaries with "Type" and "Severity"
    :rtype: list of dict
    """
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
