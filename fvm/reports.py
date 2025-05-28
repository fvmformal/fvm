import os
import subprocess
from datetime import datetime

from fvm import generate_test_cases
from fvm.parsers import parse_reports

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
                                log = f'{framework.outdir}/{design}/{step}.log',
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
        logger.info(f'Results directory already exists, moving it from {framework.resultsdir} to {framework.resultsdir}_{timestamp}')
        shutil.move(framework.resultsdir, f'{framework.resultsdir}_{timestamp}')
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
                    reachability_rpt_path = f'{framework.outdir}/{design}/covercheck_verify.rpt'
                    reachability_html_path = f'{framework.outdir}/{design}/reachability.html'
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
                    properties = generate_test_cases.parse_log_to_json(f'{framework.outdir}/{design}/{step}.log')
                    property_summary = generate_test_cases.parse_property_summary(f'{framework.outdir}/{design}/{step}.log')
                if step == 'prove.formalcover':
                    formal_signoff_html = None
                    if not framework.is_disabled('observability'):
                        observability_rpt_path = f'{framework.outdir}/{design}/formal_observability.rpt'
                        observability_html_path = f'{framework.outdir}/{design}/formal_observability.html'
                        if os.path.exists(observability_rpt_path):
                            parse_reports.parse_formal_observability_report_to_html(observability_rpt_path, observability_html_path)
                            observability_html = observability_html_path
                        else:
                            observability_html = None
                    if not framework.is_disabled('reachability'):
                        formal_reachability_rpt_path = f'{framework.outdir}/{design}/formal_reachability.rpt'
                        formal_reachability_html_path = f'{framework.outdir}/{design}/formal_reachability.html'
                        if os.path.exists(formal_reachability_rpt_path):
                            parse_reports.parse_formal_reachability_report_to_html(formal_reachability_rpt_path, formal_reachability_html_path)
                            formal_reachability_html = formal_reachability_html_path
                        else:
                            formal_reachability_html = None
                    if not framework.is_disabled('signoff'):
                        formal_signoff_rpt_path = f'{framework.outdir}/{design}/formal_signoff.rpt'
                        formal_signoff_html_path = f'{framework.outdir}/{design}/formal_signoff.html'
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

