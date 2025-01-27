import uuid
import json
import os
import shutil 
import re

def generate_test_case(design_name, step, status="passed", start_time=None, stop_time=None,
                       stdout=None, property_summary=None, reachability_html=None, friendliness_score=None,
                       observability_html=None, formal_reachability_html=None, formal_signoff_html=None):
    """
    Generate a test case structure for reports.
    """
    test_case_uuid = str(uuid.uuid4())
    history_id = str(uuid.uuid4()) 
    test_case_id = str(uuid.uuid4()) 

    full_name = f"fvm_out/{design_name}/{step}.log"
    name = f"{design_name}.{step}"

    description=f"This is the step {step} of FVM"

    if step == "prove":
        summary_markdown = ""
        asserts_value = None
        covers_value = None
        
        for key, value in property_summary.items():
            if key == "Asserts": 
                asserts_value = value
                summary_markdown += f"- **{key}**: {value}\n"
            elif key == "Covers": 
                covers_value = value
                summary_markdown += f"- **{key}**: {value}\n"
            elif isinstance(value, dict): 
                if key == "Assertions":
                    for subkey, subvalue in value.items():
                        percentage = (subvalue / asserts_value) * 100
                        summary_markdown += f"  - **{subkey}**: {subvalue}/{asserts_value} ({percentage:.2f}%)\n"
                elif key == "Cover":  
                    for subkey, subvalue in value.items():
                        percentage = (subvalue / covers_value) * 100
                        summary_markdown += f"  - **{subkey}**: {subvalue}/{covers_value} ({percentage:.2f}%)\n"
            else:
                summary_markdown += f"- **{key}**: {value}\n"

        summary_markdown = summary_markdown if summary_markdown else "No property summary available."

        description = f"{description}\n\n### Property Summary\n{summary_markdown}"

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
            "value": design_name
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
        elif status.lower() == "passed" and step == "friendliness" and friendliness_score != None:
            friendliness_score = round(friendliness_score, 2)
            status_details = {
                "known": False,
                "muted": False,
                "flaky": False,
                "message": f"The friendliness score for design '{design_name}' is {friendliness_score}%."
            }

        attachment_uuid = str(uuid.uuid4())
        if step != "prove.simcover":
            try:
                output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.log"
                original_file = f"fvm_out/{design_name}/{step}.log" 
                shutil.copy(original_file, output_attachment_file)
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
                if reachability_html != None:
                    if os.path.exists(reachability_html):
                        attachment_uuid = str(uuid.uuid4()) 
                        try:
                            output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.html"
                            original_file = reachability_html
                            shutil.copy(original_file, output_attachment_file)
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
            elif step == 'prove':
                if formal_reachability_html != None:
                    if os.path.exists(formal_reachability_html):
                        attachment_uuid = str(uuid.uuid4()) 
                        try:
                            output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.html"
                            original_file = formal_reachability_html
                            shutil.copy(original_file, output_attachment_file)
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
                if observability_html != None:
                    if os.path.exists(observability_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.html"
                            original_file = observability_html
                            shutil.copy(original_file, output_attachment_file)
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
                if formal_signoff_html != None:
                    if os.path.exists(formal_signoff_html):
                        attachment_uuid = str(uuid.uuid4())
                        try:
                            output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.html"
                            original_file = formal_signoff_html
                            shutil.copy(original_file, output_attachment_file)
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
        else:
            attachment_uuid = str(uuid.uuid4())
            output_attachment_file = f"fvm_out/dashboard/allure-results/{attachment_uuid}-attachment.log"
            with open(output_attachment_file, "w") as log_file:
                log_file.write(stdout)
            attachments = [
                {
                    "name": f"{step}.log",
                    "source": f"{attachment_uuid}-attachment.log",
                    "type": "text/plain"
                }
            ]

    test_case = {
        "uuid": test_case_uuid,
        "historyId": history_id,
        "testCaseId": test_case_id,
        "fullName": full_name,
        "name": name,
        "description": description,
        "links": links,
        "labels": labels,
        "status": status,
        "start": start_time,
        "stop": stop_time
    }

    if status_details:
        test_case["statusDetails"] = status_details

    if status.lower() != "skipped":
        test_case["attachments"] = attachments

    output_file = f"fvm_out/dashboard/allure-results/{test_case_uuid}-result.json"
    with open(output_file, 'w') as json_file:
        json.dump(test_case, json_file, indent=2)

def parse_property_summary(file_path):
    """
    Parse the 'Property Summary' section from the given file.
    """
    summary = {}
    start_marker = "# ========================================\n# Property Summary                   Count\n# ========================================\n"
    end_marker = "# Message"

    with open(file_path, 'r') as file:
        content = file.read()

    start_index = content.find(start_marker)
    if start_index == -1:
        raise ValueError("Property Summary section not found in the file.")

    summary_section = content[start_index + len(start_marker):]
    end_index = summary_section.find(end_marker)
    if end_index == -1:
        raise ValueError("End of Property Summary section not found.")
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

