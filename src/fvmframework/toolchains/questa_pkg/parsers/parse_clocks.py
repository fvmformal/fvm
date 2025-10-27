"""
Parser for clocks step results.

This module extracts checks and organizes them by
categories such as Violations, Cautions, Evaluations, etc.

It is specifically for Questa CDC results.
"""
import re

def parse_clocks_results(file_path):
    """
    Parse a clocks step results file and return a dictionary with check details.

    :param file_path: Path to the clocks results file.
    :type file_path: str
    :return: Dictionary with categories and their check details.
    :rtype: dict
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()


    category_pattern = re.compile(
        r'(Violations|Cautions|Evaluations|Resolved - Waived or Verified Status|Proven|Filtered)'
        r'\s*\((\d+)\)\n'
        r'-----------------------------------------------------------------\n'
        r'([\s\S]*?)\n\n',
        re.DOTALL
    )

    categories = category_pattern.findall(content)

    clocks_results = {
        "Violations": {"count": 0, "checks": {}},
        "Cautions": {"count": 0, "checks": {}},
        "Evaluations": {"count": 0, "checks": {}},
        "Resolved - Waived or Verified Status": {"count": 0, "checks": {}},
        "Proven": {"count": 0, "checks": {}},
        "Filtered": {"count": 0, "checks": {}}
    }

    for category in categories:
        category_name = category[0]
        category_count = int(category[1])

        raw_details = category[2].strip()
        category_details = raw_details.split('\n') if raw_details != "<None>" else []

        clocks_results[category_name]["count"] = category_count

        for detail in category_details:
            check_pattern = re.match(r'(.+?)\s*\((\d+)\)', detail.strip())
            if check_pattern:
                check_name = check_pattern.group(1).strip()
                check_count = int(check_pattern.group(2))
                clocks_results[category_name]["checks"][check_name] = check_count

    return clocks_results
