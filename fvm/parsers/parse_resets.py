import re

def parse_resets_results(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    rdc_summary_pattern = re.compile(
        r'Total number of checks:\s*\((\d+)\)'
    )
    category_pattern = re.compile(
        r'(Violation|Caution|Evaluation|Resolved - Waived or Verified Status|Filtered)\s*\((\d+)\)\n'
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
        category_details = category[2].strip().split('\n') if category[2].strip() != "<None>" else []

        resets_results[category_name]["count"] = category_count

        for detail in category_details:
            check_pattern = re.match(r'(.+?)\s*\((\d+)\)', detail.strip())
            if check_pattern:
                check_name = check_pattern.group(1).strip()
                check_count = int(check_pattern.group(2))
                resets_results[category_name]["checks"][check_name] = check_count

    return resets_results
