import re

def parse_targets_report(report_path):
    results = {}
    current_section = None
    capture = False

    with open(report_path, "r") as f:
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
    # TODO: Check if there are more categories
    mapping = {
        "Targets Proven": "Proven",
        "Targets Vacuously Proven": "Vacuous",
        "Targets Fired": "Fired",
        "Targets Fired with Warning": "Fired with Warning",
        "Targets Covered": "Covered",
        "Targets Covered with Warning": "Covered with Warning",
        "Targets Uncoverable": "Uncoverable",
        "Targets Inconclusive": "Inconclusive",
    }
    normalized = {}
    for key, value in data.items():
        clean_key = re.sub(r"\s*\(\d+\)", "", key).strip()
        final_key = mapping.get(clean_key, clean_key)
        normalized[final_key] = value
    return normalized