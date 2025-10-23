"""Generate test case structures for reports."""
import uuid
import json
import os
import shutil
import re

def generate_test_case(design_name, prefix, step, results_dir, status="passed", outdir=None,
                       start_time=None, stop_time=None, friendliness_score=None,
                       properties = None, step_summary_html = None, html_files=None):
    """
    Generate a test case structure for reports.

    :param design_name: Name of the design.
    :type design_name: str
    :param prefix: Prefix for the test case ID.
    :type prefix: str
    :param step: Name of the step.
    :type step: str
    :param results_dir: Directory to store results.
    :type results_dir: str
    :param status: Status of the test case (default is "passed").
    :type status: str
    :param start_time: Start time in milliseconds since epoch.
    :type start_time: int
    :param stop_time: Stop time in milliseconds since epoch.
    :type stop_time: int
    :param friendliness_score: Friendliness score (optional).
    :type friendliness_score: float or None
    :param properties: JSON string of properties (optional).
    :type properties: str or None
    :param step_summary_html: Path to HTML summary file (optional).
    :type step_summary_html: str or None
    :param html_files: List of additional HTML files to attach (optional).
    :type html_files: list of str or None
    """
    test_case_uuid = str(uuid.uuid4())
    history_id = f"{prefix}.{design_name}.{step}"
    test_case_id = f"{prefix}.{design_name}.{step}_id"

    full_name = os.path.join(outdir, design_name, step, f"{step}.log")
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
    attachment = os.path.join(results_dir, f"{attachment_uuid}-attachment.log")
    original_file = os.path.join(outdir, design_name, step, f"{step}.log")
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
            attachment = os.path.join(results_dir, f"{attachment_uuid}-attachment.html")
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
        if properties is not None:
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

    output_file = os.path.join(results_dir, f"{test_case_uuid}-result.json")
    with open(output_file, 'w', encoding="utf-8") as json_file:
        json.dump(test_case, json_file, indent=2)

def html_to_oneline(html_file):
    """Convert an HTML file to a single line string, preserving <pre> blocks."""
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(r"<pre.*?>.*?</pre>", lambda m: m.group(0), html, flags=re.DOTALL)

    def remove_outside_pre(text):
        parts = re.split(r"(<pre.*?>.*?</pre>)", text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if not part.startswith("<pre"):
                parts[i] = part.replace("\n", "")
        return "".join(parts)

    html_oneline = remove_outside_pre(html)

    return html_oneline
