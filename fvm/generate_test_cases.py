import uuid
import json
import os
import shutil
import re
from datetime import datetime

def generate_test_case(design_name, prefix, step, results_dir, status="passed",
                       start_time=None, stop_time=None, friendliness_score=None,
                       properties = None, step_summary_html = None, html_files=None):
    """
    Generate a test case structure for reports.
    """
    test_case_uuid = str(uuid.uuid4())
    history_id = f"{prefix}.{design_name}.{step}"
    test_case_id = f"{prefix}.{design_name}.{step}_id"

    full_name = f"fvm_out/{design_name}/{step}/{step}.log"
    name = f"{design_name}.{step}"

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

    # Attachments
    attachments = []

    # Add standard output attachment
    attachment_uuid = str(uuid.uuid4())
    attachment = f"{results_dir}/{attachment_uuid}-attachment.log"
    original_file = f"fvm_out/{design_name}/{step}/{step}.log"
    if os.path.exists(original_file):
        shutil.copy(original_file, attachment)

        attachments.append(
            {
                "name": f"{step}.log",
                "source": f"{attachment_uuid}-attachment.log",
                "type": "text/plain"
            }
        )

    # Add HTML attachments
    if html_files:
        for original_file in html_files:
            attachment_uuid = str(uuid.uuid4())
            attachment = f"{results_dir}/{attachment_uuid}-attachment.html"
            if os.path.exists(original_file):
                shutil.copy(original_file, attachment)
                attachments.append(
                    {
                        "name": os.path.basename(original_file),
                        "source": f"{attachment_uuid}-attachment.html",
                        "type": "text/html"
                    }
                )

    steps = []
    if step == "prove":
        properties = json.loads(properties)

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

    output_file = f"{results_dir}/{test_case_uuid}-result.json"
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
