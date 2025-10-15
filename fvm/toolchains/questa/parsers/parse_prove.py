"""Parsers for Prove reports."""
import re
import json
from datetime import datetime

def parse_targets_report(report_path):
    """
    Parses the targets report and extracts relevant information.
    """
    results = {}
    current_section = None
    capture = False

    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Detect section start
            if line.startswith("Targets "):
                current_section = line
                results[current_section] = []
                capture = True
                continue

            # Stop capturing only when another section starts
            if capture and line.startswith("Assumptions"):
                capture = False
                current_section = None
                continue

            # Capture targets if we're in a section
            if capture and line and not line.startswith("-"):
                results[current_section].append(line)

    summary = {}
    for section, items in results.items():
        summary[section] = {
            "count": len(items),
            "items": items
        }

    return summary

def normalize_sections(data):
    """
    Normalizes section names to a standard format.
    """
    mapping = {
        "Targets Proven": "Proven",
        "Targets Vacuously Proven": "Vacuous",
        "Targets Fired": "Fired",
        "Targets Fired with Warning": "Fired with Warning",
        "Targets Fired with Warnings": "Fired with Warning",
        "Targets Covered": "Covered",
        "Targets Covered with Warning": "Covered with Warning",
        "Targets Covered with Warnings": "Covered with Warning",
        "Targets Uncoverable": "Uncoverable",
        "Targets Inconclusive": "Inconclusive",
    }
    normalized = {}
    for key, value in data.items():
        clean_key = re.sub(r"\s*\(\d+\)", "", key).strip()
        final_key = mapping.get(clean_key, clean_key)
        normalized[final_key] = value
    return normalized

def parse_property_summary(file_path):
    """
    Parse the 'Property Summary' section from the given file.
    """
    summary = {}
    start_marker = "# ========================================\n# "
    start_marker += "Property Summary                   "
    start_marker += "Count\n# ========================================\n"
    end_marker = "# Message"

    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()

    start_index = content.find(start_marker)
    if start_index == -1:
        summary["Error"] = "Property Summary section not found."
        return summary

    summary_section = content[start_index + len(start_marker):]
    end_index = summary_section.find(end_marker)
    if end_index == -1:
        summary["Error"] = "End of Property Summary section not found."
        return summary

    summary_section = summary_section[:end_index]
    current_category = None
    for line in summary_section.splitlines():
        if re.match(r"# [-=]+", line) or not line.strip():
            continue

        match = re.match(r"#\s+(\w+)\s+(\d+)", line)
        if match:
            key, value = match.groups()
            value = int(value)
            if key == 'Assumes':
                summary['Assumes'] = value
                current_category = None
            elif key == 'Asserts':
                summary['Asserts'] = value
                current_category = 'Assertions'
            elif key == 'Covers':
                summary['Covers'] = value
                current_category = 'Cover'
            else:
                if current_category:
                    if current_category not in summary:
                        summary[current_category] = {}
                    summary[current_category][key] = value
        elif "# ----------------------------------------" in line:
            continue
        elif "# ========================================" in line:
            current_category = None

    return summary

def parse_properties_extended(log_file):
    """
    Parses the properties from a log file and categorizes them.
    """
    results = {
        "Proven": [],
        "Covered": [],
        "Vacuity Check Passed": [],
        "Fired": [],
        "Vacuity Check Failed": [],
        "Uncoverable": []
    }

    inconclusive_entries = {}

    pattern = re.compile(
        r"^# \[(\d{2}:\d{2}:\d{2})\]\s+(Proven|Covered|Vacuity Check Passed|"
        r"Fired|Vacuity Check Failed|Uncoverable):\s+([A-Za-z0-9_.]+)"
        r"\s*\(engine:(\d+)(?:, vacuity check:([\w]+))?(?:, radius:(-?\d+))?\)"
    )

    def time_to_seconds(time_str):
        """Converts time in format HH:MM:SS to seconds"""
        t = datetime.strptime(time_str, "%H:%M:%S")
        return t.hour * 3600 + t.minute * 60 + t.second

    with open(log_file, "r", encoding="utf-8") as file:
        for line in file:
            if "--------- Process Statistics ----------" in line:
                break

            match = pattern.search(line)
            if match:
                time, category, assertion, engine, vacuity_check, radius = match.groups()
                engine = int(engine)
                entry = {
                    "time": time_to_seconds(time),  
                    "assertion": assertion,
                    "engine": engine
                }
                if vacuity_check:
                    entry["vacuity_check"] = vacuity_check
                if radius:
                    entry["radius"] = int(radius)

                if category == "Proven" and vacuity_check == "inconclusive":
                    inconclusive_entries[assertion] = entry

                if category == "Vacuity Check Passed":
                    key = assertion
                    if key in inconclusive_entries:
                        inconclusive_entries[key]["vacuity_check"] = "passed"
                        del inconclusive_entries[key]
                elif category == "Vacuity Check Failed":
                    key = assertion
                    if key in inconclusive_entries:
                        inconclusive_entries[key]["vacuity_check"] = "failed"
                        del inconclusive_entries[key]
                else:
                    results[category].append(entry)

    return json.dumps(results, indent=4)


def property_summary(file_path):
    """
    Parses a property summary from a log file and organizes the data in a hierarchical structure.

    :param file_path: Path to the log file to be parsed.
    :return: A dictionary containing the parsed property summary data.
    """
    # Regular expressions to extract information
    property_pattern = re.compile(r'(.+?)\s+(\d+)')
    sub_property_pattern = re.compile(r'\s{2}(.+?)\s+\((\d+)\)')

    log_data = {}

    # Flag to indicate if we are in the "Property Summary" section
    in_property_summary = False

    # Variables to handle the hierarchy
    current_parent = None

    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if we are in the "Property Summary" section
        if "Property Summary" in line:
            in_property_summary = True
            i += 1
            continue

        # If we are in the "Property Summary" section, process the lines
        if in_property_summary:
            if line.startswith("==="):
                if (i + 2 < len(lines) and lines[i + 1].strip() == "" and
                    lines[i + 2].strip() == ""):
                    break

            # If we find a separation line (---), start capturing children
            if line.startswith("---"):
                i += 1
                continue

            # Skip empty lines
            if line == "":
                i += 1
                continue

            # Look for main properties
            property_match = property_pattern.match(lines[i])
            if property_match:
                property_name = property_match.group(1).strip()
                property_count = int(property_match.group(2))

                # If there is no current parent, it's a main property
                if current_parent is None or lines[i - 1].startswith("==="):
                    log_data[property_name] = {'Count': property_count}
                    current_parent = property_name
                else:
                    # If there is a current parent, it's a child property
                    if 'Children' not in log_data[current_parent]:
                        log_data[current_parent]['Children'] = {}
                    log_data[current_parent]['Children'][property_name] = {'Count': property_count}

            # Look for sub-properties (lines with double indentation)
            sub_property_match = sub_property_pattern.match(lines[i])
            if sub_property_match:
                sub_property_name = sub_property_match.group(1).strip()
                count = int(sub_property_match.group(2))
                # Assign the sub-property to the last child of the current parent
                if current_parent and 'Children' in log_data[current_parent]:
                    last_child = list(log_data[current_parent]['Children'].keys())[-1]
                    log_data[current_parent]['Children'][last_child][sub_property_name] = count

        i += 1

    return log_data
