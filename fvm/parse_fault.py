import re

def parse_fault_summary(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    assumes_pattern = re.compile(
        r'Assumes\s*(\d+)\s*\n'
        r'(?:\s*Property\s*\((\d+)\)\s*\n)?' 
        r'(?:\s*Mapping\s*\((\d+)\)\s*\n)?', 
        re.DOTALL
    )

    targets_pattern = re.compile(
        r'Targets\s*(\d+)\s*\n'
        r'----------------------------------------\s*\n'
        r'(?:Proven\s*(\d+)\s*\n)?'
        r'(?:Fired\s*(\d+)\s*\n)?',
        re.DOTALL
    )

    assumes_match = assumes_pattern.search(content)
    assumes_data = {
        "Total": int(assumes_match.group(1)) if assumes_match else 0,
        "Property": int(assumes_match.group(2)) if assumes_match and assumes_match.group(2) else 0,
        "Mapping": int(assumes_match.group(3)) if assumes_match and assumes_match.group(3) else 0
    }

    targets_match = targets_pattern.search(content)
    targets_data = {
        "Total": int(targets_match.group(1)) if targets_match else 0,
        "Proven": int(targets_match.group(2)) if targets_match else 0,
        "Fired": int(targets_match.group(3)) if targets_match and targets_match.group(3) else 0
    }

    slec_summary = {
        "Assumes": assumes_data,
        "Targets": targets_data
    }

    return slec_summary
