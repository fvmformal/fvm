"""
Parser for resets step results.

This module extracts checks and organizes them by
categories such as Violation, Caution, Evaluation, etc.

It is specifically for Questa RDC results.
"""
import re

def parse_resets_results(file_path):
    """
    Parse a resets step results file and return a dictionary with check details.

    :param file_path: Path to the resets results file.
    :type file_path: str
    :return: Dictionary with categories and their check details.
    :rtype: dict
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    category_pattern = re.compile(
        r'(Violation|Caution|Evaluation|Resolved - Waived or Verified Status|Filtered)\s*'
        r'\((\d+)\)\n'
        r'-----------------------------------------------------------------\n'
        r'([\s\S]*?)\n\n',
        re.DOTALL
    )

    categories = category_pattern.findall(content)

    resets_results = {
        "Violation": {"count": 0, "checks": {}},
        "Caution": {"count": 0, "checks": {}},
        "Evaluation": {"count": 0, "checks": {}},
        "Resolved - Waived or Verified Status": {"count": 0, "checks": {}},
        "Filtered": {"count": 0, "checks": {}}
    }

    for category in categories:
        category_name = category[0]
        category_count = int(category[1])

        raw_details = category[2].strip()
        category_details = raw_details.split('\n') if raw_details != "<None>" else []

        resets_results[category_name]["count"] = category_count

        for detail in category_details:
            check_pattern = re.match(r'(.+?)\s*\((\d+)\)', detail.strip())
            if check_pattern:
                check_name = check_pattern.group(1).strip()
                check_count = int(check_pattern.group(2))
                resets_results[category_name]["checks"][check_name] = check_count

    return resets_results
