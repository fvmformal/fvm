import os
import subprocess
from datetime import datetime
from rich.console import Console

from fvm import helpers
from fvm import generate_test_cases
from fvm.parsers import parse_formal_signoff
from fvm.parsers import parse_reachability
from fvm.parsers import parse_reports
from fvm.parsers import parse_simcover
from fvm.parsers import parse_lint
from fvm.parsers import parse_rulecheck
from fvm.parsers import parse_xverify
from fvm.parsers import parse_resets
from fvm.parsers import parse_clocks
from fvm.parsers import parse_fault

# TODO: these constants (FVM_STEPS and FVM_POST_STEPS) are redundant and we
# will remove them soon, but for now while we are refactoring we need them so
# the build doesn't fail. After the refactor, we should get the steps and
# post_steps from framework.steps
# Steps, in order of execution, of the methodology
FVM_STEPS = [
    'lint',
    'friendliness',
    'rulecheck',
    'xverify',
    'reachability',
    'fault',
    'resets',
    'clocks',
    'prove'
    ]

FVM_POST_STEPS = [
    'prove.formalcover',
    'prove.simcover'
    ]

def pretty_summary(framework, logger):
    """Prints the final summary"""
    # TODO : use rich or a similar python package to format a table
    # TODO : print the status for each design.step
    # TODO : color the status
    # TODO : print also number of warnings and errors, and all relevant
    # information from PropCheck (number of
    # assume/assert/fired/proven/cover/covered/uncoverable/etc. For this,
    # we may need to post-process the prove step log
    # TODO : print elapsed time
    from rich.table import Table
    from rich.measure import Measurement
    from rich.box import ROUNDED

    summary_console = Console(force_terminal=True, force_interactive=False,
                              record=True)
    summary_console.rule(f'[bold white]FVM Summary[/bold white]')

    # Calculate maximum length of {design}.{step} so we can pad later
    maxlen = 0
    for design in framework.designs:
        for step in FVM_STEPS + FVM_POST_STEPS:
            curlen = len(f'{design}.{step}')
            if curlen > maxlen:
                maxlen = curlen

    # Accumulators for total values
    total_time = 0
    total_pass = 0
    total_fail = 0
    total_skip = 0
    total_broken = 0
    total_cont = 0
    total_stat = 0

    #text_header = Text("==== Summary ==============================================")
    #summary_console.print(text_header)
    table = None
    for design in framework.designs:
        table = None
        table = Table(title=f"[cyan]FVM Summary: {design}[/cyan]")
        table.add_column("status", justify="left", min_width=6)
        table.add_column("step", justify="left", min_width=25)
        table.add_column("results", justify="right", min_width=5)
        table.add_column("elapsed time", justify="right", min_width=12)
        for step in FVM_STEPS + FVM_POST_STEPS:
            total_cont += 1
            # Only print pass/fail/skip, the rest of steps where not
            # selected by the user so there is no need to be redundant
            if 'status' in framework.results[design][step]:
                total_stat += 1
                status = framework.results[design][step]['status']
                #text = Text()
                #text.append(status, style=style)
                #text.append(' ')
                design_step = f'{design}.{step}'
                #text.append(f'{design_step:<{maxlen}}')

                result_str_for_table = ""
                score_str =  '                '
                step_summary = getattr(framework, f"{step}_summary", {})
                if step_summary and ("Error" in step_summary or "Violation" in step_summary or 
                                        "Violations" in step_summary or "Corruptible" in step_summary):
                    step_errors = step_summary.get('Error', {}).get('count', 0)
                    step_warnings = step_summary.get('Warning', {}).get('count', 0)
                    step_violation = step_summary.get('Violation', {}).get('count', 0)
                    step_caution = step_summary.get('Caution', {}).get('count', 0)
                    step_inconclusives = step_summary.get('Inconclusive', {}).get('count', 0)
                    step_violations = step_summary.get('Violations', {}).get('count', 0)
                    step_cautions = step_summary.get('Cautions', {}).get('count', 0)
                    step_proven = step_summary.get('Proven', {}).get('count', 0)
                    step_corruptibles = step_summary.get('Corruptible', {}).get('count', 0)
                    step_incorruptibles = step_summary.get('Incorruptible', {}).get('count', 0)

                    if step_errors != 0:
                        result_str_for_table += f"[bold red]{step_errors}E[/bold red]"
                        status = 'fail'
                    if step_violation != 0:
                        result_str_for_table += f"[bold red]{step_violation}V[/bold red]"
                        status = 'fail'
                    if step_violations != 0:
                        result_str_for_table += f"[bold red]{step_violations}V[/bold red]"
                        status = 'fail'
                    if step_corruptibles != 0:
                        result_str_for_table += f"[bold red]{step_corruptibles}C[/bold red]"
                        status = 'fail'
                    if step_warnings != 0:
                        result_str_for_table += f"[bold yellow] {step_warnings}W[/bold yellow]"
                    if step_caution != 0:
                        result_str_for_table += f"[bold yellow] {step_caution}C[/bold yellow]"
                    if step_cautions != 0:
                        result_str_for_table += f"[bold yellow] {step_cautions}C[/bold yellow]"
                    if step_incorruptibles != 0:
                        result_str_for_table += f"[bold yellow] {step_incorruptibles}I[/bold yellow]"
                    if step_inconclusives != 0:
                        result_str_for_table += f"[bold white] {step_inconclusives}I[/bold white]"
                    if step_proven != 0:
                        result_str_for_table += f"[bold green] {step_proven}P[/bold green]"
                    if (step_errors == 0 and step_warnings == 0 and step_violation == 0 and step_caution == 0 and 
                        step_inconclusives == 0 and step_violations == 0 and step_cautions == 0 and step_proven == 0 and
                        step_corruptibles == 0 and step_incorruptibles == 0):
                        result_str_for_table += "[bold green]ok[/bold green]"
                elif "score" in framework.results[design][step]:
                        result_str_for_table += f"[bold green]{framework.results[design][step]['score']:.2f}%[/bold green]"
                elif step == 'reachability':
                    if framework.reachability_summary:
                        ## TODO: change status to follow this?
                        any_fail = any(row.get("Status") == "fail" for row in framework.reachability_summary)

                        for row in framework.reachability_summary:
                            if row.get("Coverage Type") == "Total":
                                percentage = row.get("Percentage", "N/A")

                                if any_fail:
                                    result_str_for_table = f"[bold red]{percentage}[/bold red]"
                                else:
                                    result_str_for_table = f"[bold green]{percentage}[/bold green]"

                                break
                    else:
                        result_str_for_table = "N/A"
                elif step == 'fault':
                    if framework.fault_summary:
                        fault_summary = framework.fault_summary
                        fault_total_targets = fault_summary["Targets"]["Total"]
                        fault_total_proven = fault_summary["Targets"]["Proven"]
                        if fault_total_targets == fault_total_proven:
                            result_str_for_table += f"[bold green]{fault_total_proven}/{fault_total_targets}[/bold green]"
                        else:
                            result_str_for_table += f"[bold red]{fault_total_proven}/{fault_total_targets}[/bold red]"
                            status = 'fail'
                    else:
                        result_str_for_table = "N/A"
                elif step == 'prove.formalcover':
                    if framework.formalcover_summary:
                        score = next( (float(entry["Covered (P)"].split("(")[-1].strip(" %)"))
                               for entry in framework.formalcover_summary["data"]
                               if entry.get("Coverage Type") == "Total"), 0.0)
                        if status == 'pass':
                            result_str_for_table = f'[bold green]{score}%[/bold green]'
                        else:
                            result_str_for_table = f'[bold red]{score}%[/bold red]'
                    else:
                        result_str_for_table = "N/A"
                elif step == 'prove.simcover':
                    if framework.simcover_summary:
                        score = framework.simcover_summary.get("Total", {}).get("percentage", 0)
                        if status == 'pass':
                            result_str_for_table = f'[bold green]{score}[/bold green]'
                        else:
                            result_str_for_table = f'[bold red]{score}[/bold red]'
                    else:
                        result_str_for_table = "N/A"
                elif step != 'prove':
                    result_str_for_table = "N/A"

                time_str_for_table = "N/A"
                if "elapsed_time" in framework.results[design][step]:
                    time = framework.results[design][step]["elapsed_time"]
                    total_time += time
                    time_str = f' ({helpers.readable_time(time)})'
                    time_str_for_table = helpers.readable_time(time)
                    #text.append(time_str)
                #text.append(f' result={framework.results[design][step]}', style='white')
                #summary_console.print(text)
                if status == 'pass':
                    style = 'bold green'
                    total_pass += 1
                elif status == 'fail':
                    style = 'bold red'
                    total_fail += 1
                elif status == 'skip':
                    style = 'bold yellow'
                    total_skip += 1
                elif status == 'broken':
                    style = 'bold yellow'
                    total_broken += 1
                table.add_row(f'[{style}]{status}[/{style}]',
                              f'{step}', result_str_for_table,
                              time_str_for_table)
                #print(f'{status} {design}.{step}, result={framework.results[design][step]}')

                if step == "prove" and framework.property_summary:
                    # TODO: Change framework.property_summary to framework.results[design][step]["property_summary"]
                    prop_summary = framework.property_summary
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

                    table.add_row("", f"  [{color_asserts}]Asserts[/{color_asserts}]", str(asserts), "")


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
                        table.add_row("", f"    └ {key}", f"[{color_asserts_children}]{formatted_str}[/{color_asserts_children}]", "")

                        for subkey, subval in value.items():
                            if subkey != "Count":
                                subcount = subval
                                formatted_substr = f"{subcount}/{count}" if count else f"{subcount}/0"
                                color_asserts_children = color_map_asserts.get(subkey, "bold green")
                                table.add_row("", f"       └ {subkey}", f"[{color_asserts_children}]{formatted_substr}[/{color_asserts_children}]", "")

                    covers_children = prop_summary.get("Covers", {}).get("Children", {})
                    uncovered_count = covers_children.get("Uncoverable", {}).get("Count", 0)
                    not_a_target_count = covers_children.get("Not a Target", {}).get("Count", 0)

                    if uncovered_count > 0:
                        color_covers = "bold red"
                    elif not_a_target_count > 0:
                        color_covers = "bold white"
                    else:
                        color_covers = "bold green"

                    color_map_covers = {
                        "Covered": "bold green",
                        "Uncoverable": "bold red",
                        "Not a Target": "bold white",
                        "Covered with Warning": "bold yellow",
                        "Covered without Waveform": "bold yellow"
                        }

                    table.add_row("", f"  [{color_covers}]Covers[/{color_covers}]", str(covers), "")
                    for key, value in covers_children.items():
                        count = value.get("Count", 0)
                        formatted_str = f"{count}/{covers}" if covers else f"{count}/0"
                        color_covers_children = color_map_covers.get(key, "bold green")
                        table.add_row("", f"    └ {key}", f"[{color_covers_children}]{formatted_str}[/{color_covers_children}]", "")

                        for subkey, subval in value.items():
                            if subkey != "Count":
                                subcount = subval
                                formatted_substr = f"{subcount}/{count}" if count else f"{subcount}/0"
                                color_covers_children = color_map_covers.get(subkey, "bold green")
                                table.add_row("", f"       └ {subkey}", f"[{color_covers_children}]{formatted_substr}[/{color_covers_children}]", "")
        summary_console.print(table)

    #text_footer = Text("===========================================================")
    #console.print(text_footer)
    #text = Text()
    #text.append('pass', style='bold green')
    #text.append(f' {total_pass} of {total_cont}')
    #summary_console.print(text)
    summary = f"[bold green]  pass[/bold green] {total_pass} of {total_cont}\n"
    if total_fail != 0:
        #text = Text()
        #text.append('fail', style='bold red')
        #text.append(f' {total_fail} of {total_cont}')
        #summary_console.print(text)
        summary += f"[bold red]  fail[/bold red] {total_fail} of {total_cont}\n"
    if total_skip != 0:
        #text = Text()
        #text.append('skip', style='bold yellow')
        #text.append(f' {total_skip} of {total_cont}')
        #summary_console.print(text)
        summary += f"[bold yellow]  skip[/bold yellow] {total_skip} of {total_cont}\n"
    if total_broken != 0:
        #text = Text()
        #text.append('broken', style='bold yellow')
        #text.append(f' {total_broken} of {total_cont}')
        #summary_console.print(text)
        summary += f"[bold yellow]  broken[/bold yellow] {total_broken} of {total_cont}\n"
    if total_stat != total_cont:
        #text = Text()
        #text.append('omit', style='bold white')
        #text.append(f' {total_cont - total_stat} of {total_cont} (not executed due to early exit)')
        #summary_console.print(text)
        summary += f"[bold white]  omit[/bold white] {total_cont - total_stat} of {total_cont}\n"
    #summary_console.print(text_footer)
    #text = Text()
    #text.append(f'Total time  : {helpers.readable_time(total_time)}\n')
    #text.append(f'Elapsed time: (not yet implemented)')
    #summary_console.print(text)
    #summary_console.print(text_footer)
    #summary_console.print(table)

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
        summary_console.save_html(f'{framework.outdir}/summary.html')
    else:
        logger.error(f'Cannot access output directory {framework.outdir}, something went wrong')

# TODO: separate functionality in at least two functions, maybe three:
#       - generate_xml_report
#       - generate_text_report (not sure we really need a text report)
#       - generate_html_report
def generate_reports(framework, logger):
    """Generates output reports"""
    # TODO : move this import to the top of the new file (for example,
    # reports.py)
    from junit_xml import TestSuite, TestCase, to_xml_report_string
    # For all designs:
    #   Define a TestSuite per design
    #   For all steps:
    #     Define a TestCase per step
    testsuites = list()
    for design in framework.designs:
        testcases = list()
        for step in FVM_STEPS + FVM_POST_STEPS:
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
                                log = f'{framework.outdir}/{design}/{step}/{step}.log',
                                url = None
                                )

            # TODO : we can have status == 'error' for when something
            # breaks and the tests are not actually executed. Not sure we
            # need that here, but let's keep this note just in case. We
            # would use testcase.add_error_info if I recall correctly

            # output argument is an optional, non-standard field
            # TODO : maybe we could just put the first line in message and
            # all the errors in output, but Allure is supposed to render
            # the full message even if it has more than one line of text
            if status == 'fail':
                logger.info(f'{design}.{step} failed')
                message = framework.results[design][step]['message']
                #print(f'{message=}')
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
    # error in fvmframework.setup(). But we will generate the directory and
    # the report nevertheless, because CI tools may depend on the report
    # being there.
    xml_string = to_xml_report_string(testsuites, prettyprint=True)

    # Since junit_xml doesn't support adding a name to the global
    # testsuites set, we will modify the generated xml string before
    # commiting it to a file
    xml_string = xml_string.replace("<testsuites", f'<testsuites name="{framework.scriptname}"')

    # TODO : we should use os.path.join or pathlib instead of concatenating
    # directory separators (our approach is not cross platform). Apparently
    # pathlib is recommended for new projects instead of os.path, and both
    # approaches are cross-platform
    xmlfile = framework.scriptname.replace('/','_')
    if xmlfile.startswith('_'):
        xmlfile = xmlfile[1:]
    xmlfile, extension = os.path.splitext(xmlfile)
    xmlfile = f'{framework.resultsdir}/{xmlfile}'
    xmlfile = xmlfile + '.xml'

    # If the results directory exist, try to enable Allure history
    # For this, we are going to:
    #   1. Move the already-existing results directory out of the way. We
    #   will create a new name for it using a timestamp
    #   TODO : we should create the timestamp when we create the directory,
    #   not when we move it
    #   2. Create a new results directory
    #   3. If a reportdir exits, copy its history to the new results
    #   directory
    #   4. Remove the reportdir
    #   5. Generate the XML results in the new results directory
    # This should make the history available so the next call to "allure
    # generate" can find it

    import shutil
    if os.path.isdir(framework.resultsdir):
        timestamp = datetime.now().isoformat()
        logger.info(f'Results directory already exists, moving it from {framework.resultsdir} to {framework.outdir}/fvm_history/{timestamp}')
        shutil.move(framework.resultsdir, f'{framework.outdir}/fvm_history/{timestamp}')
        os.makedirs(framework.resultsdir, exist_ok=True)
        historydir = f'{framework.reportdir}/history'
        if os.path.isdir(historydir):
            logger.info(f'Report history directory already exists, moving it from {historydir} to {framework.resultsdir}/history')
            shutil.move(historydir, f'{framework.resultsdir}/history')
            logger.info(f'Removing old report directory at {framework.resultsdir}')
            shutil.rmtree(framework.reportdir)

    os.makedirs(framework.resultsdir, exist_ok=True)
    with open(xmlfile, 'w') as f:
        f.write(xml_string)

    # TODO : move this to generate_html_reports function
    import shutil

    if shutil.which('allure') is not None:
        # We normalize the path because the Popen documentation recommends
        # to pass a fully qualified (absolute) path, and it also states
        # that shutil.which() returns unqualified paths
        allure_exec = os.path.abspath(shutil.which('allure'))
        cmd = [allure_exec, 'generate', framework.resultsdir, '-o', framework.reportdir]
        logger.info(f'Generating dashboard with {cmd=}')
        process = subprocess.Popen (cmd,
                                    stdout  = subprocess.PIPE,
                                    stderr  = subprocess.PIPE,
                                    text    = True,
                                    bufsize = 1
                                    )
        # Wait for the process to complete and get the return code
        # TODO : fail if retval is not zero
        retval = process.wait()
    else:
        logger.warning("""allure is not found in $(PATH), cannot generate
        HTML reports. If you are running inside a venv and have created the
        venv with the Makefile, you should have allure inside your venv
        folder. If you are not using a venv, you should install allure by
        running 'python3 install_allure.py [install_dir], and add its bin/
        directory to your $PATH'""")

    # TODO : better manage this log
    verbose = True

    stdout_lines = list()
    stderr_lines = list()
    # TODO : the following line fails if the Allure process was not
    # launched
    with process.stdout as stdout, process.stderr as stderr:
        for line in iter(stdout.readline, ''):
            # If verbose, print to console
            if verbose:
                err, warn, success = framework.linecheck(line)
                if err:
                    logger.error(line.rstrip())
                elif warn:
                    logger.warning(line.rstrip())
                elif success:
                    logger.success(line.rstrip())
                else:
                    logger.info(line.rstrip())
                    #logger.trace(line.rstrip())
            # If not verbose, print dots
            else:
                print('.', end='', flush=True)
            stdout_lines.append(line)  # Save to list

        for line in iter(stderr.readline, ''):
            # If verbose, print to console
            if verbose:
                err, warn, success = framework.linecheck(line)
                if err:
                    logger.error(line.rstrip())
                elif warn:
                    logger.warning(line.rstrip())
                elif success:
                    logger.success(line.rstrip())
                else:
                    logger.info(line.rstrip())
                    #logger.trace(line.rstrip())
            # If not verbose, print dots
            else:
                print('.', end='', flush=True)
            stderr_lines.append(line)  # Save to list

    # TODO : to see the report:
    #   allure open fvm_out/dashboard

def generate_allure(framework, logger):

    framework.clear_directory("fvm_out/dashboard/allure-results")
    file_path = "fvm_out/dashboard"
    os.makedirs(file_path, exist_ok=True)
    file_path = "fvm_out/dashboard/allure-results"
    os.makedirs(file_path, exist_ok=True)
    file_path = "fvm_out/dashboard/allure-report"
    os.makedirs(file_path, exist_ok=True)

    for design in framework.designs:
        for step in FVM_STEPS + FVM_POST_STEPS:
            if 'status' in framework.results[design][step] and framework.results[design][step]['status'] != "skip":
                status = framework.results[design][step]['status']
                custom_status_string = None
                if framework.results[design][step]['status'] == "pass":
                    status = "passed"
                elif framework.results[design][step]['status'] == "fail":
                    status = "failed"
                start_time_str = framework.results[design][step]['timestamp']
                start_time_obj = datetime.fromisoformat(start_time_str)
                start_time_sec = start_time_obj.timestamp()
                start_time = int(start_time_sec * 1000)
                stop_time = start_time + framework.results[design][step]["elapsed_time"] * 1000
                if 'stdout' in framework.results[design][step]:
                    stdout = framework.results[design][step]['stdout']
                if step == 'reachability':
                    reachability_rpt_path = f'{framework.outdir}/{design}/{step}/covercheck_verify.rpt'
                    reachability_html_path = f'{framework.outdir}/{design}/{step}/reachability.html'
                    if os.path.exists(reachability_rpt_path):
                        parse_reports.parse_reachability_report_to_html(reachability_rpt_path, reachability_html_path)
                        reachability_html = reachability_html_path
                    else:
                        reachability_html = None
                else:
                    reachability_html = None
                if step == 'friendliness' and status == "passed":
                    friendliness_score = framework.results[design][step]['score']
                else:
                    friendliness_score = None
                observability_html = None
                formal_reachability_html = None
                formal_signoff_html = None
                properties = None
                property_summary = None
                if step == 'prove':
                    properties = generate_test_cases.parse_log_to_json(f'{framework.outdir}/{design}/{step}/{step}.log')
                    property_summary = generate_test_cases.parse_property_summary(f'{framework.outdir}/{design}/{step}/{step}.log')
                if step == 'prove.formalcover':
                    formal_signoff_html = None
                    if not framework.is_disabled('observability'):
                        observability_rpt_path = f'{framework.outdir}/{design}/{step}/formal_observability.rpt'
                        observability_html_path = f'{framework.outdir}/{design}/{step}/formal_observability.html'
                        if os.path.exists(observability_rpt_path):
                            parse_reports.parse_formal_observability_report_to_html(observability_rpt_path, observability_html_path)
                            observability_html = observability_html_path
                        else:
                            observability_html = None
                    if not framework.is_disabled('reachability'):
                        formal_reachability_rpt_path = f'{framework.outdir}/{design}/{step}/formal_reachability.rpt'
                        formal_reachability_html_path = f'{framework.outdir}/{design}/{step}/formal_reachability.html'
                        if os.path.exists(formal_reachability_rpt_path):
                            parse_reports.parse_formal_reachability_report_to_html(formal_reachability_rpt_path, formal_reachability_html_path)
                            formal_reachability_html = formal_reachability_html_path
                        else:
                            formal_reachability_html = None
                    if not framework.is_disabled('signoff'):
                        formal_signoff_rpt_path = f'{framework.outdir}/{design}/{step}/formal_signoff.rpt'
                        formal_signoff_html_path = f'{framework.outdir}/{design}/{step}/formal_signoff.html'
                        if os.path.exists(formal_signoff_rpt_path):
                            parse_reports.parse_formal_signoff_report_to_html(formal_signoff_rpt_path, formal_signoff_html_path)
                            formal_signoff_html = formal_signoff_html_path
                        else:
                            formal_signoff_html = None
                else:
                    observability_html = None
                    formal_reachability_html = None
                    formal_signoff_html = None
                generate_test_cases.generate_test_case( design, status=status,
                                                        start_time=start_time, stop_time=stop_time, step=step,
                                                        stdout = stdout, property_summary = property_summary,
                                                        reachability_html = reachability_html,
                                                        friendliness_score=friendliness_score,
                                                        observability_html=observability_html,
                                                        formal_reachability_html=formal_reachability_html,
                                                        formal_signoff_html=formal_signoff_html,
                                                        properties=properties)
            elif 'status' in framework.results[design][step] and framework.results[design][step]['status'] == "skip":
                status = "skipped"
                start_time_str = datetime.now().isoformat()
                start_time_obj = datetime.fromisoformat(framework.start_time_setup)
                start_time_sec = start_time_obj.timestamp()
                start_time = int(start_time_sec * 1000)
                generate_test_cases.generate_test_case( design, status=status,
                                                        start_time=start_time, stop_time=start_time, step=step)
            else:
                status = 'omit'


    import shutil

    if shutil.which('allure') is not None:
        # We normalize the path because the Popen documentation recommends
        # to pass a fully qualified (absolute) path, and it also states
        # that shutil.which() returns unqualified paths
        allure_res = f'{framework.outdir}/dashboard/allure-results'
        allure_rep = f'{framework.outdir}/dashboard/allure-report'
        allure_exec = os.path.abspath(shutil.which('allure'))
        cmd = [allure_exec, 'generate', allure_res, '-o', allure_rep]
        logger.info(f'Generating dashboard with {cmd=}')
        process = subprocess.Popen (cmd,
                                    stdout  = subprocess.PIPE,
                                    stderr  = subprocess.PIPE,
                                    text    = True,
                                    bufsize = 1
                                    )
        # Wait for the process to complete and get the return code
        # TODO : fail if retval is not zero
        retval = process.wait()
    else:
        logger.warning("""allure is not found in $(PATH), cannot generate
        HTML reports. If you are running inside a venv and have created the
        venv with the Makefile, you should have allure inside your venv
        folder. If you are not using a venv, you should install allure by
        running 'python3 install_allure.py [install_dir], and add its bin/
        directory to your $PATH'""")

