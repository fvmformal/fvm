import re

def parse_check_summary(file_path):

    with open(file_path, "r") as file:
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

    warning_match = warning_pattern.search(file_content)
    if warning_match:
        warning_text = warning_match.group(0)
        result["Warning"]["count"] = int(re.search(r'\| Warning \((\d+)\) \|', warning_text).group(1))
        checks = check_pattern.findall(warning_text)
        result["Warning"]["checks"] = {check[0]: int(check[1]) for check in checks}

    info_match = info_pattern.search(file_content)
    if info_match:
        info_text = info_match.group(0)
        result["Info"]["count"] = int(re.search(r'\| Info \((\d+)\) \|', info_text).group(1))
        checks = check_pattern.findall(info_text)
        result["Info"]["checks"] = {check[0]: int(check[1]) for check in checks}

    resolved_match = resolved_pattern.search(file_content)
    if resolved_match:
        result["Resolved"]["count"] = int(resolved_match.group(1))

    return result
