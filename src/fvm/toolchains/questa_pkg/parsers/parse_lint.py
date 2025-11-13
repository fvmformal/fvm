"""
Parser for lint reports.

This module provides functions to parse checks with their severities and counts.

It is specifically for Questa Lint results.
"""
import re

def parse_check_summary(file_path):
    """
    Parse a lint summary file and return counts and individual check details.

    :param file_path: Path to the lint summary file to parse.
    :type file_path: str
    :return: Dictionary containing counts and check details for each category.

        Example structure::

            {
                "Error": {"count": int},
                "Warning": {"count": int, "checks": {"check_name": int, ...}},
                "Info": {"count": int, "checks": {"check_name": int, ...}},
                "Resolved": {"count": int}
            }

    :rtype: dict
    """
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    error_pattern = re.compile(r'\| Error \((\d+)\) \|')
    warning_pattern = re.compile(r'\| Warning \((\d+)\) \|[\s\S]*?(?=\| \w+ \(\d+\) \||\Z)')
    info_pattern = re.compile(r'\| Info \((\d+)\) \|[\s\S]*?(?=\| \w+ \(\d+\) \||\Z)')
    resolved_pattern = re.compile(r'\| Resolved \((\d+)\) \|')
    check_pattern = re.compile(r'^\s*(\w+)\s*:\s*(\d+)$', re.MULTILINE)

    result = {
        "Error": {},
        "Warning": {},
        "Info": {},
        "Resolved": {}
    }

    error_match = error_pattern.search(file_content)
    if error_match:
        result["Error"]["count"] = int(error_match.group(1))

    match = warning_pattern.search(file_content)
    if match:
        warning_text = match.group(0)
        count_match = re.search(r"\| Warning \((\d+)\) \|", warning_text)
        if count_match:
            result["Warning"]["count"] = int(count_match.group(1))
        checks = check_pattern.findall(warning_text)
        result["Warning"]["checks"] = {check[0]: int(check[1]) for check in checks}

    match = info_pattern.search(file_content)
    if match:
        info_text = match.group(0)
        result["Info"]["count"] = int(re.search(r'\| Info \((\d+)\) \|', info_text).group(1))
        checks = check_pattern.findall(info_text)
        result["Info"]["checks"] = {check[0]: int(check[1]) for check in checks}

    match = resolved_pattern.search(file_content)
    if match:
        result["Resolved"]["count"] = int(match.group(1))

    return result
