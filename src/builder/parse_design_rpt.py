import re
from rich.console import Console
from rich.table import Table

def get_design_summary(filename):
    summary = []
    found = False
    with open(filename, "r") as f:
        # Get all lines between "Design Summary" and
        # "User-specified Constant Bits"
        for line in f:
            if "Design Summary" in line:
                found = True
            if found:
                summary.append(line)
            if "User-specified Constant Bits" in line:
                break
    return summary

def parse_design_summary(summary):
    data = []
    for line in summary:
        match = re.match(r'^( {0,2})(.*\S)\s+(\d+)$', line)
        if match:
            # Capture leading spaces to determine category level
            leading_spaces = match.group(1)
            category = 'Subcategory' if len(leading_spaces) == 2 else 'Top-level'
            statistic = match.group(2).strip()
            count = int(match.group(3))
            data.append([category, statistic, count])
        elif "Storage Structures" in line:
            # This is a special case because it depends on what is below
            category = "Top-level"
            statistic = "Storage Structures"
            count = 'see below'
            data.append([category, statistic, count])
    return data

def update_storage_structures(data):
    # Since the report doesn't include the total number of storage structures,
    # let's add it
    total = 0
    # Get the total
    search_terms = ["Counters", "FSMs", "RAMs"]
    for row in data:
        for term in search_terms:
            if term in row[1] :
                total += row[2]
    # Update the relevant field
    for row in data:
        if "Storage Structures" in row[1]:
            row[2] = total
    return data

def data_from_design_summary(filename):
    summary = get_design_summary(filename)
    data = parse_design_summary(summary)
    data = update_storage_structures(data)
    return data

