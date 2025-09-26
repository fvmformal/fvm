import uuid
import json
import os
import shutil
import re
from datetime import datetime

def generate_test_case(design_name, prefix, step, results_dir, status="passed", start_time=None,
                       stop_time=None, stdout=None, property_summary=None,
                       reachability_html=None, friendliness_score=None, observability_html=None,
                       formal_reachability_html=None, formal_signoff_html=None,
                       properties = None, step_summary_html = None):
    """
    Generate a test case structure for reports.
    """
    test_case_uuid = str(uuid.uuid4())
    history_id = f"{prefix}.{design_name}.{step}"
    test_case_id = f"{prefix}.{design_name}.{step}_id"

    full_name = f"fvm_out/{design_name}/{step}/{step}.log"
    name = f"{design_name}.{step}"

    allure_results_dir = results_dir

    if step_summary_html is not None:
        desc_key = "descriptionHtml"
        description = html_to_oneline(step_summary_html)
    else:
        desc_key = "description"
        description=f"This is the step {step} of FVM"

    links = [
        {
            "type": "link",
            "name": "Documentation",
            "url": "https://docs.example.com/testUserLogin"
        }
    ]

    labels = [
        {
            "name": "framework",
            "value": "FVM"
        },
        {
            "name": "epic",
            "value": step  
        },
        {
            "name": "parentSuite",
            "value": f"{prefix}.{design_name}"
        },
        {
            "name": "package",
            "value": step  
        }
    ]

    status_details = None
    if status.lower() == "skipped":
        status_details = {
            "known": False,
            "muted": False,
            "flaky": False,
            "message": f"The FVM step {step} was skipped for design '{design_name}'.",
            "trace": "Skipped due to unmet conditions or manual override."
        }
    else:
        if status.lower() == "failed":
            status_details = {
                "known": False,
                "muted": False,
                "flaky": False,
                "message": f"The FVM step {step} failed for design '{design_name}'.",
                "trace": "Failure due to critical issues or build errors."
            }
        elif (status.lower() == "passed" and
              step == "friendliness" and
              friendliness_score is not None):
            friendliness_score = round(friendliness_score, 2)
            status_details = {
                "known": False,
                "muted": False,
                "flaky": False,
                "message": f"The friendliness score for design "
                           f"'{design_name}' is {friendliness_score}%."
            }

        attachment_uuid = str(uuid.uuid4())
        if step not in ('prove.simcover', 'prove.formalcover'):
            try:
                attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.log"
                original_file = f"fvm_out/{design_name}/{step}/{step}.log"
                shutil.copy(original_file, attachment)
            except FileNotFoundError:
                return

            attachments = [
                {
                    "name": f"{step}.log",
                    "source": f"{attachment_uuid}-attachment.log",
                    "type": "text/plain"
                }
            ]

            if step == 'reachability':
                if reachability_html is not None:
                    if os.path.exists(reachability_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.html"
                            original_file = reachability_html
                            shutil.copy(original_file, attachment)
                        except FileNotFoundError:
                            print(f"Error: Input log file {original_file} not found.")
                            return
                        attachments.append(
                            {
                            "name": "reachability.html",
                            "source": f"{attachment_uuid}-attachment.html",
                            "type": "text/html"
                            }
                        )
        else:
            attachments = []
            if step == 'prove.formalcover':
                if formal_reachability_html is not None:
                    if os.path.exists(formal_reachability_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.html"
                            original_file = formal_reachability_html
                            shutil.copy(original_file, attachment)
                        except FileNotFoundError:
                            print(f"Error: Input log file {original_file} not found.")
                            return
                        attachments.append(
                            {
                            "name": "formal_reachability.html",
                            "source": f"{attachment_uuid}-attachment.html",
                            "type": "text/html"
                            }
                        )
                if observability_html is not None:
                    if os.path.exists(observability_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.html"
                            original_file = observability_html
                            shutil.copy(original_file, attachment)
                        except FileNotFoundError:
                            print(f"Error: Input log file {original_file} not found.")
                            return
                        attachments.append(
                            {
                            "name": "formal_observability.html",
                            "source": f"{attachment_uuid}-attachment.html",
                            "type": "text/html"
                            }
                        )
                if formal_signoff_html is not None:
                    if os.path.exists(formal_signoff_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.html"
                            original_file = formal_signoff_html
                            shutil.copy(original_file, attachment)
                        except FileNotFoundError:
                            print(f"Error: Input log file {original_file} not found.")
                            return
                        attachments.append(
                            {
                            "name": "formal_signoff.html",
                            "source": f"{attachment_uuid}-attachment.html",
                            "type": "text/html"
                            }
                        )
            attachment_uuid = str(uuid.uuid4())
            attachment = f"{allure_results_dir}/{attachment_uuid}-attachment.log"
            with open(attachment, "w", encoding="utf-8") as log_file:
                log_file.write(stdout)
            attachments.append(
                {
                    "name": f"{step}.log",
                    "source": f"{attachment_uuid}-attachment.log",
                    "type": "text/plain"
                }
            )

    if step == "prove":
        properties = json.loads(properties)
        steps = []

        for entry in properties.get("Proven", []):
            assertion_name = entry.get("assertion", "unknown")
            vacuity_check = entry.get("vacuity_check", "unknown")
            entry_time = entry.get("time", 0)
            step_in_steps ={
                "name": "Assertion: " + assertion_name,  
                "status": "broken" if vacuity_check == "failed" else "passed", 
                "start": start_time,
                "stop": start_time + entry_time * 1000,    
                "steps": []
            }

            steps.append(step_in_steps)

        for entry in properties.get("Fired", []):
            steps.append({
                "name": "Assertion: " + entry["assertion"],  
                "status": "failed",          
                "start": start_time,
                "stop": start_time + entry["time"] * 1000
            })

        for entry in properties.get("Covered", []):
            steps.append({
                "name": "Cover: " + entry["assertion"],  
                "status": "passed",          
                "start": start_time,
                "stop": start_time + entry["time"] * 1000
            })

        for entry in properties.get("Uncoverable", []):
            steps.append({
                "name": "Cover: " + entry["assertion"],  
                "status": "failed",          
                "start": start_time,
                "stop": start_time + entry["time"] * 1000
            })

    else:
        steps = []

    test_case = {
        "uuid": test_case_uuid,
        "historyId": history_id,
        "testCaseId": test_case_id,
        "fullName": full_name,
        "name": name,
        desc_key: description,
        "links": links,
        "labels": labels,
        "status": status,
        "start": start_time,
        "stop": stop_time,
        "steps": steps
    }

    if status_details:
        test_case["statusDetails"] = status_details

    if status.lower() != "skipped":
        test_case["attachments"] = attachments

    output_file = f"{allure_results_dir}/{test_case_uuid}-result.json"
    with open(output_file, 'w', encoding="utf-8") as json_file:
        json.dump(test_case, json_file, indent=2)

def html_to_oneline(html_file):
    import re

    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(r"<pre.*?>.*?</pre>", lambda m: m.group(0), html, flags=re.DOTALL)

    def remove_outside_pre(text):
        parts = re.split(r"(<pre.*?>.*?</pre>)", text, flags=re.DOTALL)
        for i in range(len(parts)):
            if not parts[i].startswith("<pre"):
                parts[i] = parts[i].replace("\n", "")
        return "".join(parts)

    html_oneline = remove_outside_pre(html)

    return html_oneline

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

def parse_log_to_json(log_file):
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
        """Convierte el tiempo en formato HH:MM:SS a segundos"""
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
