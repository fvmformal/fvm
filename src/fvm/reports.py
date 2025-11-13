"""Report generation functions for FVM"""
import os
import re
import subprocess
import shutil
import signal
import importlib.resources

from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.measure import Measurement
from junit_xml import TestSuite, TestCase, to_xml_report_string

from fvm import helpers
from fvm import generate_test_cases
from fvm import manage_allure
from fvm.toolchains.questa_pkg.parsers import parse_prove

def get_all_steps(steps, post_steps):
    """
    Generate a list of steps including post-steps.

    :param steps: List of main steps.
    :type steps: list of str
    :param post_steps: Dictionary mapping main steps to their post-steps.
    :type post_steps: dict of str to list of str

    :return: List of all steps including post-steps.
    :rtype: list of str
    """
    all_steps = []
    for step in steps:
        all_steps.append(step)
        if step in post_steps:
            for post_step in post_steps[step]:
                all_steps.append(f"{step}.{post_step}")
    return all_steps

def rich_table_to_markdown(rich_table_str):
    """
    Convert a rich Table to a Markdown table.

    :param rich_table_str: The string representation of a rich Table.
    :type rich_table_str: str

    :return: Markdown table as a string.
    :rtype: str
    """
    rows = []
    for line in rich_table_str.splitlines():
        line = line.strip()
        if not line or line[0] in ("┏", "┡", "└", "┘", "┬", "┴", "╇", "╋"):
            continue
        if not any(c in line for c in ("│", "┃")):
            continue

        line = line.replace("┃", "│")

        parts = line.split("│")[1:-1]
        cells = [p.strip() for p in parts]

        if any(cells):
            rows.append(cells)

    if not rows:
        return ""

    num_cols = len(rows[0])
    for r in rows:
        if len(r) < num_cols:
            r.extend([""] * (num_cols - len(r)))

    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * num_cols) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows[1:]]

    return "\n".join([header, separator] + body)

def pretty_summary(framework, logger):
    """
    Prints the final summary

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param logger: the logger object
    :type logger: loguru._logger.Logger
    """
    console = Console(force_terminal=True, force_interactive=False,
                              record=True)
    console.rule('[bold white]FVM Summary[/bold white]')

    summary_console = Console(force_terminal=True, force_interactive=False,
                              record=True)

    # Accumulators for total values
    total_time = 0
    total_pass = 0
    total_fail = 0
    total_skip = 0
    total_cont = 0
    total_stat = 0

    def colorize(color, text):
        return f"[bold {color}]{text}[/bold {color}]"

    table = None
    for design in framework.designs:
        table = None
        table = Table(title=f"[cyan]FVM {helpers.get_fvm_version()} Summary: {design}[/cyan]")
        table.add_column("status", justify="left", min_width=6)
        table.add_column("step", justify="left", min_width=25)
        table.add_column("results", justify="right", min_width=5)
        table.add_column("elapsed time", justify="right", min_width=12)
        all_steps = get_all_steps(framework.steps.steps, framework.steps.post_steps)
        for step in all_steps:
            total_cont += 1
            # Only print pass/fail/skip, the rest of steps where not
            # selected by the user so there is no need to be redundant
            if 'status' in framework.results[design][step]:
                total_stat += 1
                status = framework.results[design][step]['status']

                result_str = ""
                step_summary = framework.results[design][step].get('summary', None)
                # Error/Warning summaries
                if step_summary and ("Error" in step_summary or "Violation" in step_summary or
                                     "Violations" in step_summary
                                     or "Corruptible" in step_summary):
                    step_errors = step_summary.get('Error', {}).get('count', 0)
                    step_warnings = step_summary.get('Warning', {}).get('count', 0)
                    step_violation = step_summary.get('Violation', {}).get('count', 0)
                    step_caution = step_summary.get('Caution', {}).get('count', 0)
                    step_inconclusives = step_summary.get('Inconclusive', {}).get('count', 0)
                    step_violations = step_summary.get('Violations', {}).get('count', 0)
                    step_cautions = step_summary.get('Cautions', {}).get('count', 0)
                    step_proven = step_summary.get('Proven', {}).get('count', 0)
                    step_corruptibles = step_summary.get('Corruptible', {}).get('count', 0)
                    step_incorruptible = step_summary.get('Incorruptible', {}).get('count', 0)

                    if step_errors != 0:
                        result_str += f"[bold red] {step_errors}E[/bold red]"
                        status = 'fail'
                    if step_violation != 0:
                        result_str += f"[bold red] {step_violation}V[/bold red]"
                        status = 'fail'
                    if step_violations != 0:
                        result_str += f"[bold red] {step_violations}V[/bold red]"
                        status = 'fail'
                    if step_corruptibles != 0:
                        result_str += f"[bold red] {step_corruptibles}C[/bold red]"
                        status = 'fail'
                    if step_warnings != 0:
                        result_str += f"[bold yellow] {step_warnings}W[/bold yellow]"
                    if step_caution != 0:
                        result_str += f"[bold yellow] {step_caution}C[/bold yellow]"
                    if step_cautions != 0:
                        result_str += f"[bold yellow] {step_cautions}C[/bold yellow]"
                    if step_incorruptible != 0:
                        result_str += f"[bold yellow] {step_incorruptible}I[/bold yellow]"
                    if step_inconclusives != 0:
                        result_str += f"[bold white] {step_inconclusives}I[/bold white]"
                    if step_proven != 0:
                        result_str += f"[bold green] {step_proven}P[/bold green]"
                    if (step_errors == 0 and step_warnings == 0 and step_violation == 0 and
                        step_caution == 0 and step_inconclusives == 0 and step_violations == 0
                        and step_cautions == 0 and step_proven == 0 and step_corruptibles == 0
                        and step_incorruptible == 0):
                        result_str += "[bold green]ok[/bold green]"
                # Friendliness summary
                elif "score" in framework.results[design][step]:
                    friendliness = framework.results[design][step]['score']
                    result_str += f"[bold green]{friendliness:.2f}%[/bold green]"
                # Coverage summaries
                elif isinstance(step_summary, list):
                    if step_summary and "Coverage Type" in step_summary[0]:
                        any_fail = any(row.get("Status") == "fail" for row in step_summary)

                        for row in step_summary:
                            if row.get("Coverage Type") == "Total":
                                percentage = row.get("Percentage", "N/A")

                                if any_fail:
                                    result_str = f"[bold red]{percentage}[/bold red]"
                                else:
                                    result_str = f"[bold green]{percentage}[/bold green]"

                                break
                    else:
                        result_str = "N/A"
                elif step != 'prove':
                    result_str = "N/A"

                time_str_for_table = "N/A"
                if "elapsed_time" in framework.results[design][step]:
                    time = framework.results[design][step]["elapsed_time"]
                    total_time += time
                    time_str_for_table = helpers.readable_time(time)

                if status == 'pass':
                    style = 'bold green'
                    total_pass += 1
                elif status == 'fail':
                    style = 'bold red'
                    total_fail += 1
                elif status == 'skip':
                    style = 'bold yellow'
                    total_skip += 1
                else:
                    style = 'bold white'

                table.add_row(f'[{style}]{status}[/{style}]',
                              f'{step}', result_str,
                              time_str_for_table)

                if step == "prove" and step_summary:
                    prop_summary = step_summary
                    assumes = prop_summary.get("Assumes", {}).get("Count", 0)
                    asserts = prop_summary.get("Asserts", {}).get("Count", 0)
                    covers = prop_summary.get("Covers", {}).get("Count", 0)

                    table.add_row("", "  Assumes", str(assumes), "")

                    asserts_children = prop_summary.get("Asserts", {}).get("Children", {})
                    failed_count = asserts_children.get("Fired", {}).get("Count", 0)
                    inconclusive_count = asserts_children.get("Inconclusive", {}).get("Count", 0)
                    proven_data = asserts_children.get("Proven", {}).get("Children", {})
                    vacuous_count = proven_data.get("Vacuous", {}).get("Count", 0)

                    if failed_count > 0:
                        color_asserts = "bold red"
                    elif inconclusive_count > 0:
                        color_asserts = "bold white"
                    elif vacuous_count > 0:
                        color_asserts = "bold yellow"
                    else:
                        color_asserts = "bold green"

                    table.add_row("", f"  [{color_asserts}]Asserts[/{color_asserts}]",
                                  str(asserts), "")

                    color_map_asserts = {
                        "Proven": "bold green",
                        "Fired": "bold red",
                        "Inconclusive": "bold white",
                        "Vacuous": "bold yellow",
                        "Proven with Warning": "bold yellow",
                        "Fired with Warning": "bold yellow",
                        "Fired without Waveform": "bold red"
                        }

                    for key, value in asserts_children.items():
                        count = value.get("Count", 0)
                        formatted_str = f"{count}/{asserts}" if asserts else f"{count}/0"
                        color_asserts_children = color_map_asserts.get(key, "bold green")
                        colored = colorize(color_asserts_children, formatted_str)
                        table.add_row("", f"    └ {key}", colored, "")

                        for subkey, subval in value.items():
                            if subkey != "Count":
                                formatted_substr = f"{subval}/{count}" if count else f"{subval}/0"
                                color_asserts_children = color_map_asserts.get(subkey,"bold green")
                                colored = colorize(color_asserts_children, formatted_substr)
                                table.add_row("", f"       └ {subkey}", colored, "")

                    covers_children = prop_summary.get("Covers", {}).get("Children", {})
                    uncovered_count = covers_children.get("Uncoverable", {}).get("Count", 0)
                    inconclusive_count = covers_children.get("Inconclusive", {}).get("Count", 0)
                    not_a_target_count = covers_children.get("Not a Target", {}).get("Count", 0)

                    if uncovered_count > 0:
                        color_covers = "bold red"
                    elif not_a_target_count > 0 or inconclusive_count > 0:
                        color_covers = "bold white"
                    else:
                        color_covers = "bold green"

                    color_map_covers = {
                        "Covered": "bold green",
                        "Uncoverable": "bold red",
                        "Not a Target": "bold white",
                        "Inconclusive": "bold white",
                        "Covered with Warning": "bold yellow",
                        "Covered without Waveform": "bold yellow"
                        }

                    table.add_row("",
                                  f"  [{color_covers}]Covers[/{color_covers}]",
                                  str(covers),
                                  "")
                    for key, value in covers_children.items():
                        count = value.get("Count", 0)
                        formatted_str = f"{count}/{covers}" if covers else f"{count}/0"
                        color_covers_children = color_map_covers.get(key, "bold green")
                        table.add_row("",
                                      f"    └ {key}",
                                      colorize(color_covers_children, formatted_str),
                                      "")

                        for subkey, subval in value.items():
                            if subkey != "Count":
                                formatted_substr = f"{subval}/{count}" if count else f"{subval}/0"
                                color_covers_children = color_map_covers.get(subkey, "bold green")
                                table.add_row("",
                                              f"       └ {subkey}",
                                              colorize(color_covers_children, formatted_substr),
                                              "")
        summary_console.print(table)

    summary = f"[bold green]  pass[/bold green] {total_pass} of {total_cont}\n"
    if total_fail != 0:
        summary += f"[bold red]  fail[/bold red] {total_fail} of {total_cont}\n"
    if total_skip != 0:
        summary += f"[bold yellow]  skip[/bold yellow] {total_skip} of {total_cont}\n"
    if total_stat != total_cont:
        summary += f"[bold white]  omit[/bold white] {total_cont - total_stat} of {total_cont}\n"

    console_options = summary_console.options
    if table is not None:
        table_width = Measurement.get(summary_console, console_options, table).maximum
    else:
        table_width = 0
    separator_line = " "
    separator_line += "─" * table_width
    summary += f"{separator_line}\n"
    summary += f"{'  Total time:'} [bold cyan]{helpers.readable_time(total_time)}[/bold cyan]\n"
    summary_console.print(summary)
    # If framework.outdir doesn't exist, something went wrong: in that case, do
    # not try to save the HTML summary
    if os.path.isdir(framework.outdir):
        summary_console.save_html(os.path.join(framework.outdir, 'summary.html'), clear=False)
        summary_console.save_text(os.path.join(framework.outdir, 'summary.txt'))
    else:
        logger.error(f'Cannot access output directory {framework.outdir}, something went wrong')

def generate_xml_report(framework, logger):
    """
    Generates output reports
    
    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param logger: the logger object
    :type logger: loguru._logger.Logger
    """

    # For all designs:
    #   Define a TestSuite per design
    #   For all steps:
    #     Define a TestCase per step
    testsuites = []
    for design in framework.designs:
        testcases = []
        all_steps = get_all_steps(framework.steps.steps, framework.steps.post_steps)
        for step in all_steps:
            if 'status' in framework.results[design][step]:
                status = framework.results[design][step]['status']
                custom_status_string = None
            else:
                status = 'omit'
                custom_status_string = "Not executed"

            if 'elapsed_time' in framework.results[design][step]:
                elapsed_time = framework.results[design][step]["elapsed_time"]
            else:
                elapsed_time = None

            if 'stdout' in framework.results[design][step]:
                stdout = framework.results[design][step]['stdout']
            else:
                stdout = None

            if 'stderr' in framework.results[design][step]:
                stderr = framework.results[design][step]['stderr']
            else:
                stderr = None

            if 'timestamp' in framework.results[design][step]:
                timestamp = framework.results[design][step]['timestamp']
            else:
                timestamp = None

            # status and category are optional attributes and as such they
            # will no be automatically rendered by Allure
            testcase = TestCase(name = f'{design}.{step}',
                                classname = design,
                                elapsed_sec = elapsed_time,
                                stdout = stdout,
                                stderr = stderr,
                                timestamp = timestamp,
                                status = custom_status_string,
                                category = step,
                                file = framework.scriptname,
                                line = None,
                                log = os.path.join(framework.outdir, design, step, f'{step}.log'),
                                url = None
                                )

            # output argument is an optional, non-standard field, so we'll set
            # it to None
            if status == 'fail':
                logger.trace(f'{design}.{step} failed')
                message = framework.results[design][step]['message']
                testcase.add_failure_info(message = "Error in tool log",
                                          output = None, # 'output string',
                                          failure_type = None #'error type'
                                          )

            if status == 'skip':
                testcase.add_skipped_info(message = 'Test skipped by user',
                                          output = None
                                          )

            if status == 'omit':
                testcase.add_skipped_info(message = 'Not executed due to early exit',
                                          output = None
                                          )

            testcases.append(testcase)

        testsuite = TestSuite(f'{framework.prefix}.{design}', testcases)
        testsuites.append(testsuite)

    # If the output directory doesn't exist, it is because there was an
    # error in FvmFramework.setup(). But we will generate the directory and
    # the report nevertheless, because CI tools may depend on the report
    # being there.
    xml_string = to_xml_report_string(testsuites, prettyprint=True)

    # Since junit_xml doesn't support adding a name to the global
    # testsuites set, we will modify the generated xml string before
    # commiting it to a file
    xml_string = xml_string.replace("<testsuites",
                                    f'<testsuites name="{framework.scriptname}" '
                                    f'fvm_version="{helpers.get_fvm_version()}"')

    xmlfile = f"{framework.prefix}_results"
    if xmlfile.startswith('_'):
        xmlfile = xmlfile[1:]
    xmlfile, extension = os.path.splitext(xmlfile)
    xmlfile = os.path.join(framework.resultsdir, xmlfile)
    xmlfile = xmlfile + '.xml'

    # If the results directory exist, try to enable Allure history
    # For this, we are going to:
    #   1. Move the already-existing results directory out of the way. We
    #   will create a new name for it using a timestamp
    #   2. Create a new results directory
    #   3. Generate the XML results in the new results directory
    # This should make the history available so the next call to "allure
    # generate" can find it

    if os.path.isdir(framework.resultsdir):
        timestamp = datetime.now().isoformat()
        logger.trace(f'Results directory already exists, moving it from '
                    f'{framework.resultsdir} to {os.path.join(framework.outdir, "fvm_history", timestamp)}')
        shutil.move(framework.resultsdir, os.path.join(framework.outdir, "fvm_history", timestamp))
        os.makedirs(framework.resultsdir, exist_ok=True)

    os.makedirs(framework.resultsdir, exist_ok=True)
    with open(xmlfile, 'w', encoding="utf-8") as f:
        f.write(xml_string)

def generate_html_report(framework, logger):
    """
    Generates an Allure report from the framework results

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param logger: the logger object
    :type logger: loguru._logger.Logger
    """

    dashboard_dir = os.path.join(f'{framework.outdir}', "dashboard")
    results_dir = os.path.join(dashboard_dir, framework.prefix, "results")
    report_dir = os.path.join(dashboard_dir, framework.prefix, "report")
    os.makedirs(dashboard_dir, exist_ok=True)
    if framework.showall is False and framework.shownorun is False:
        if os.path.isdir(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)

                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        os.makedirs(results_dir, exist_ok=True)

        for design in framework.designs:
            all_steps = get_all_steps(framework.steps.steps, framework.steps.post_steps)
            for step in all_steps:

                if ('status' in framework.results[design][step] and
                    framework.results[design][step]['status'] != "skip"):

                    # Default values
                    step_summary_html = None
                    html_files = []
                    status = framework.results[design][step]['status']
                    start_time = int(datetime.now().timestamp() * 1000)
                    stop_time = start_time
                    friendliness_score = None
                    properties = None

                    step_path = os.path.join(framework.outdir, design, step)
                    step_summary = f"{step}_summary.html"
                    if os.path.exists(os.path.join(step_path, step_summary)):
                        step_summary_html = os.path.join(step_path, step_summary)

                    if os.path.exists(step_path):
                        html_files = [
                            os.path.join(step_path, f)
                            for f in os.listdir(step_path)
                            if f.endswith(".html") and f != step_summary
                        ]

                    if framework.results[design][step]['status'] == "pass":
                        status = "passed"
                    elif framework.results[design][step]['status'] == "fail":
                        status = "failed"

                    if 'timestamp' in framework.results[design][step]:
                        start_time_str = framework.results[design][step]['timestamp']
                        start_time_obj = datetime.fromisoformat(start_time_str)
                        start_time_sec = start_time_obj.timestamp()
                        start_time = int(start_time_sec * 1000)
                        stop_time = start_time + framework.results[design][step]["elapsed_time"] * 1000

                    if step == 'friendliness' and 'score' in framework.results[design][step]:
                        friendliness_score = framework.results[design][step]['score']

                    if step == 'prove':
                        path = os.path.join(framework.outdir, design, step, f'{step}.log')
                        if os.path.exists(path):
                            properties = parse_prove.parse_properties_extended(path)

                    generate_test_cases.generate_test_case(design,
                                                        prefix=framework.prefix,
                                                        results_dir=results_dir,
                                                        status=status,
                                                        outdir=framework.outdir,
                                                        start_time=start_time,
                                                        stop_time=stop_time,
                                                        step=step,
                                                        friendliness_score=friendliness_score,
                                                        properties=properties,
                                                        step_summary_html=step_summary_html,
                                                        html_files=html_files
                                                        )
                elif ('status' in framework.results[design][step] and
                    framework.results[design][step]['status'] == "skip"):
                    status = "skipped"
                    start_time_str = datetime.now().isoformat()
                    start_time_obj = datetime.fromisoformat(framework.start_time_setup)
                    start_time_sec = start_time_obj.timestamp()
                    start_time = int(start_time_sec * 1000)
                    generate_test_cases.generate_test_case(design,
                                                        prefix=framework.prefix,
                                                        results_dir=results_dir,
                                                        status=status,
                                                        outdir=framework.outdir,
                                                        start_time=start_time,
                                                        stop_time=start_time,
                                                        step=step)
                else:
                    status = 'omit'

    allure_version = manage_allure.DEFAULT_ALLURE_VERSION
    allure_install_dir = os.path.join(os.path.expanduser("~"), ".cache", "fvm")
    manage_allure.ensure_allure(allure_version, allure_install_dir)
    allure_exec = Path(manage_allure.get_allure_bin_path(allure_version, allure_install_dir))

    if allure_exec.exists():
        if framework.showall:
            # Report with all designs
            global_results_dir = os.path.join(dashboard_dir, "allure-results")
            global_report_dir = os.path.join(dashboard_dir, "allure-report")
            copy_results_to_allure_results(dashboard_dir, global_results_dir)
            if os.listdir(global_results_dir):
                generate_allure(global_results_dir, global_report_dir, allure_exec, logger)
                show_allure(global_report_dir, allure_exec, logger)
            else:
                logger.error("No results found to generate the global report")
        else:
            if framework.shownorun is False:
                # Copy history if it exists
                report_history = os.path.join(report_dir, "history")
                results_history = os.path.join(results_dir, "history")
                if os.path.exists(report_history):
                    # Delete new_history if it exists
                    if os.path.exists(results_history):
                        shutil.rmtree(results_history)
                    shutil.copytree(report_history, results_history)
                if os.path.exists(results_dir):
                    retval = generate_allure(results_dir, report_dir, allure_exec, logger)
            if framework.show or framework.shownorun:
                if os.path.exists(report_dir):
                    show_allure(report_dir, allure_exec, logger)
                else:
                    logger.error("No report found to show")

    else:
        logger.error("""Cannot find the allure executable, but the framework should have installed it""")

def generate_allure(res_dir, rep_dir, allure_exec, logger):
    """Generate an Allure report"""
    cmd = [allure_exec, 'generate', '--clean', res_dir, '-o', rep_dir,
        "--name", f"FVM {helpers.get_fvm_version()} Report"]
    logger.trace(f'Generating dashboard with {cmd=}')
    process = subprocess.Popen (cmd,
                                stdout  = subprocess.PIPE,
                                stderr  = subprocess.PIPE,
                                text    = True,
                                bufsize = 1
                                )
    retval = process.wait()
    # Replace Allure favicon with FVM favicon only if Allure favicon exists
    package_data_dir = importlib.resources.files('fvm')
    if os.path.exists(os.path.join(rep_dir, 'favicon.ico')):
        shutil.copy2(os.path.join(package_data_dir, 'assets', "favicon.ico"),
                     os.path.join(rep_dir, 'favicon.ico'))
    return retval

def show_allure(directory, allure_exec, logger):
    """Show an Allure report"""
    cmd = [allure_exec, 'open', directory]
    logger.trace(f'Opening dashboard with {cmd=}')
    process = subprocess.Popen (cmd,
                                stdout  = subprocess.PIPE,
                                stderr  = subprocess.PIPE,
                                text    = True,
                                bufsize = 1
                                )
    logger.info('Opening dashboard. Close with Ctrl+C')

    # We need to close the allure process when receiving SIGINT
    def handle_sigint_allure(signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.killpg(os.getpgid(process.pid), signal.SIGINT)

    signal.signal(signal.SIGINT, handle_sigint_allure)
    retval = process.wait()
    return retval

def copy_results_to_allure_results(base_dir, dst_dir):
    """
    Copy all files in the 'results' subfolders of the subdirectories
    to the allure_results folder in base_dir, overwriting them if they exist.
    Ignore the allure_results and allure_report folders.
    """
    exclude_dirs = {"allure_results", "allure_report"}

    if os.path.isdir(dst_dir):
        shutil.rmtree(dst_dir)
    os.makedirs(dst_dir)
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # If current directory ends with "/results"
        if os.path.basename(root) == "results":
            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(dst_dir, file)
                shutil.copy2(src, dst)

def generate_text_report(framework, logger):
    """
    Generate a Markdown report from the framework results

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    """
    global_summary = []

    if framework.start_time_setup is None:
        start_time = datetime.now()
    else:
        start_time = datetime.fromisoformat(framework.start_time_setup)
    stop_time = datetime.now()

    duration = int((stop_time - start_time).total_seconds())

    duration_str = helpers.readable_time(duration)

    date_str = start_time.strftime("%d/%m/%Y")
    start_str = start_time.strftime("%-H:%M:%S")
    stop_str = stop_time.strftime("%-H:%M:%S")

    global_summary.append("# FVM Report\n")

    global_summary.append(date_str + "\n")
    global_summary.append(f"Execution time: {start_str} - {stop_str} ({duration_str})\n")
    global_summary.append(f"FVM version: {helpers.get_fvm_version()}\n")
    global_summary.append(f"Toolchain: {framework.toolchain}\n")
    global_summary.append(f"Design(s): {', '.join(framework.designs)}\n")

    for design in framework.designs:
        all_steps = get_all_steps(framework.steps.steps, framework.steps.post_steps)
        global_summary.append(f"## Design: {design}\n")
        for step in all_steps:
            md_table_str = None
            if ('status' in framework.results[design][step] and
                framework.results[design][step]['status'] != "skip"):

                # Default values
                step_summary_txt = None

                step_path = os.path.join(framework.outdir, design, step)
                step_summary_md = os.path.join(step_path, f"{step}_summary.md")

                step_summary = f"{step}_summary.txt"
                if os.path.exists(os.path.join(step_path, step_summary)):
                    step_summary_txt = os.path.join(step_path, step_summary)
                    with open(step_summary_txt, 'r', encoding='utf-8') as f:
                        rich_table_str = f.read()
                    md_table_str = rich_table_to_markdown(rich_table_str)
                    with open(step_summary_md, 'w', encoding='utf-8') as f:
                        f.write(md_table_str)


                if framework.results[design][step]['status'] == "pass":
                    status = "passed"
                elif framework.results[design][step]['status'] == "fail":
                    status = "failed"
                else:
                    status = "omit"

            elif ('status' in framework.results[design][step] and
                  framework.results[design][step]['status'] == "skip"):
                status = "skipped"
            else:
                status = 'omit'

            global_summary.append(f"### {design}.{step} [{status}]")
            if "elapsed_time" in framework.results[design][step]:
                time = framework.results[design][step]["elapsed_time"]
                time_str_for_table = helpers.readable_time(time)
                global_summary.append(f"Duration: {time_str_for_table}\n")
            logfile_path = os.path.join(framework.outdir, design, step, f"{step}.log")
            if os.path.exists(logfile_path):
                global_summary.append(f"Log file: _{logfile_path}_\n")

            pattern = re.compile(
                r"(ERROR)\s+\1.*?line='([^']+)'",
                re.DOTALL
            )

            if 'message' in framework.results[design][step]:
                matches = pattern.findall(framework.results[design][step]['message'])

                errors = [msg for level, msg in matches if level == "ERROR"]
                if errors:
                    global_summary.append("Error(s):\n")
                for e in errors:
                    global_summary.append(f"- ERROR: {e}")

            if md_table_str is not None:
                global_summary.append(md_table_str + "\n")

    path = os.path.join(framework.outdir, "summary.txt")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            rich_table_str = f.read()
        global_summary.append("## Summary")
        global_summary.append(rich_table_to_markdown(rich_table_str))

    report_path = os.path.join(framework.outdir, "text_report.md")
    logger.trace(f'Generating text report at {report_path}')
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(global_summary))
