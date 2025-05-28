import re

def parse_clocks_results(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    cdc_summary_pattern = re.compile(
        r'Total number of checks\s*\((\d+)\)'
    )
    category_pattern = re.compile(
        r'(Violations|Cautions|Evaluations|Resolved - Waived or Verified Status|Proven|Filtered)\s*\((\d+)\)\n'
        r'-----------------------------------------------------------------\n'
        r'([\s\S]*?)\n\n',
        re.DOTALL
    )

    cdc_summary_match = cdc_summary_pattern.search(content)
    total_checks = int(cdc_summary_match.group(1)) if cdc_summary_match else 0

    categories = category_pattern.findall(content)

    clocks_results = {
        "Total number of checks": total_checks,
        "Violations": {"count": 0, "details": []},
        "Cautions": {"count": 0, "details": []},
        "Evaluations": {"count": 0, "details": []},
        "Resolved - Waived or Verified Status": {"count": 0, "details": []},
        "Proven": {"count": 0, "details": []},
        "Filtered": {"count": 0, "details": []}
    }

    for category in categories:
        category_name = category[0]
        category_count = int(category[1])
        category_details = category[2].strip().split('\n') if category[2].strip() != "<None>" else []

        clocks_results[category_name]["count"] = category_count

        for detail in category_details:
            check_pattern = re.match(r'(.+?)\s*\((\d+)\)', detail.strip())
            if check_pattern:
                check_name = check_pattern.group(1).strip()
                check_count = int(check_pattern.group(2))
                clocks_results[category_name]["details"].append({
                    "check": check_name,
                    "count": check_count
                })

    return clocks_results
