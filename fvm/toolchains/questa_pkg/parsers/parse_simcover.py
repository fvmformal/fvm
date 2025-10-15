"""
Parser for simulation coverage reports.

This module provides functions to parse the coverage tables and convert them
into a unified coverage table format.

It is specifically for Questa VSim results.
"""
import re

def parse_coverage_report(input_file):
    """
    Parses the coverage report from the input file and return the results.

    :param input_file: Path to the input coverage report file.
    :return: A list of coverage data for each instance.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract headers from the first line
    headers = [h.strip() for h in re.split(r'\s{2,}', lines[0].strip())]
    coverage_results = []

    # Process each line (skipping headers and separators)
    for line in lines[2:]:
        if not line.strip():
            continue

        values = re.split(r'\s{2,}', line.strip())

        # Ensure the values list matches the header length
        if len(values) < len(headers):
            values.extend(['-'] * (len(headers) - len(values)))

        instance = values[0]

        if instance == "-zi_replay_vhdl":
            break  # Stop processing when encountering -zi_replay_vhdl

        coverage_data = {}

        # Process each header and value pair
        for i in range(1, len(headers)):
            if i >= len(values):
                coverage_data[headers[i]] = None
                continue

            match = re.match(r'(\d+\.\d+%)?\(?(\d+)/(\d+)\)?', values[i])
            if match:
                percentage = match.group(1) if match.group(1) else "-"
                covered = int(match.group(2))
                total = int(match.group(3))
                coverage_data[headers[i]] = {"percentage": percentage,
                                             "covered": covered,
                                             "total": total}
            else:
                coverage_data[headers[i]] = None if values[i] == '-' else values[i]

        coverage_results.append({"instance": instance, "coverage": coverage_data})

    return coverage_results


def sum_coverage_data(coverage_results):
    """
    Sums the coverage data across all instances and calculates percentages.

    :param coverage_results: A list of coverage data for each instance.
    :return: A dictionary containing the summed coverage data with percentages.
    """
    sum_totals = {}
    grand_total_covered = 0
    grand_total = 0

    # Mapping to normalize coverage type names between different tools
    normalize_names = {
        "Branches": "Branch",
        "Conditions": "Condition",
        "Expressions": "Expression",
        "FSM States": "FSM State",
        "FSM Transitions": "FSM Transition",
        "Statments" : "Statement",  # To catch a questa typo
        "Statements": "Statement",
        "Toggles": "Toggle",
        "Covergroup Bins": "Covergroup Bin",
    }

    # Summing coverage data for each instance
    for entry in coverage_results:
        for key, value in entry["coverage"].items():
            key = normalize_names.get(key, key) # Normalize key if needed
            if key in ["Assertions", "Directives"]:
                continue  # Exclude Assertions and Directives from the totals

            if isinstance(value, dict) and "covered" in value and "total" in value:
                if key not in sum_totals:
                    sum_totals[key] = {"covered": 0, "total": 0, "percentage": "0.00%"}

                sum_totals[key]["covered"] += value["covered"]
                sum_totals[key]["total"] += value["total"]
                grand_total_covered += value["covered"]
                grand_total += value["total"]

    # Calculate percentages for each key
    for key, data in sum_totals.items():
        if data["total"] > 0:
            percentage = (data["covered"] / data["total"]) * 100
            data["percentage"] = f"{percentage:.2f}%"

    # Add Grand Total
    if grand_total > 0:
        grand_percentage = (grand_total_covered / grand_total) * 100
    else:
        grand_percentage = 0.0

    sum_totals["Total"] = {
        "covered": grand_total_covered,
        "total": grand_total,
        "percentage": f"{grand_percentage:.2f}%"
    }

    # Sort the totals by key alphabetically
    sorted_totals = {k: sum_totals[k] for k in sorted(sum_totals)}

    return sorted_totals

def unified_format_table(table, goal=90.0):
    """Convert coverage summary table into unified table format.
    
    :param table: Coverage summary table as returned by sum_coverage_data.
    :param goal: Coverage goal percentage.
    :return: List of dictionaries with unified coverage data format.
    """
    final_data = []

    for cov_type, values in table.items():
        total = int(values.get("total", 0))
        covered = int(values.get("covered", 0))
        perc_str = values.get("percentage", "N/A")

        if total == 0:
            percentage = "N/A"
            status = "omit"
        else:
            perc_value = float(re.sub(r'%', '', perc_str))
            percentage = f"{perc_value:.1f}%"
            status = "pass" if perc_value >= goal else "fail"

        new_row = {
            "Status": status,
            "Coverage Type": cov_type,
            "Total": total,
            "Misses": total - covered,
            "Hits": covered,
            "Percentage": percentage,
            "Goal": f"{goal:.1f}%"
        }
        final_data.append(new_row)

    return final_data

def merge_coverage(sim_cov, reach_cov):
    """The simulation coverage results after excluding the unreachable elements"""
    merged = []

    reach_map = {r['Coverage Type'].lower(): r for r in reach_cov}

    for s in sim_cov:
        cov_type = s['Coverage Type']
        key = cov_type.lower()
        r = reach_map.get(key)

        unreachable = r['Unreachable'] if r else 0
        excluded = unreachable

        total = s['Total']
        effective_total = total - excluded
        hits = s['Hits']
        misses = max(s['Misses'] - excluded, 0)

        if effective_total > 0:
            percentage_value = hits / effective_total * 100
            percentage = f"{percentage_value:.1f}%"
        else:
            percentage_value = 0.0
            percentage = "N/A"

        goal = float(s['Goal'].strip('%'))
        status = 'pass' if percentage_value >= goal else 'fail'

        merged.append({
            'Coverage Type': cov_type,
            'Total': total,
            'Misses': misses,
            'Excluded': excluded,
            'Hits': hits,
            'Percentage': percentage,
            'Goal': s['Goal'],
            'Status': status
        })

    return merged