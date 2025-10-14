"""Questa toolchain for FVM"""
# Questa toolchain definition

import os
from collections import OrderedDict
import glob
import pathlib
import shutil

# TODO : are this parsers questa-specific or could they be made configurable?
# should they be moved to someplace like toolchains/questa/parsers?
from fvm.parsers import parse_formal_signoff
from fvm.parsers import parse_reachability
from fvm.parsers import parse_reports
from fvm.parsers import parse_simcover
from fvm.parsers import parse_lint
from fvm.parsers import parse_rulecheck
from fvm.parsers import parse_xverify
from fvm.parsers import parse_resets
from fvm.parsers import parse_clocks
from fvm.parsers import parse_prove
from fvm.parsers import parse_design_rpt
from fvm import helpers
from fvm import tables

# TODO : For all this file: probably forward slashes (/) are not portable and
# we should use a library to manage path operations, such as os.path or pathlib
# (pathlib seems to be more recommended). In run_friendliness we use
# os.path.join

# For the Questa tools, each tool is run through a wrapper which is the actual
# command that must be run in the command-line
# TODO : Not sure we really need this dict, although it is a nice summary
tools = {
        # step           : ["tool",       "wrapper"],
        "lint"           : ["lint",       "qverify"],
        "friendliness"   : ["autocheck",  "qverify"],
        "rulecheck"      : ["autocheck",  "qverify"],
        "xverify"        : ["xcheck",     "qverify"],
        "reachability"   : ["covercheck", "qverify"],
        "resets"         : ["rdc",        "qverify"],
        "clocks"         : ["cdc",        "qverify"],
        "prove"          : ["propcheck",  "qverify"],
        "prove.formalcover"          : ["propcheck",  "qverify"], # TODO : Decide if this is OK
#        "simulate"       : ["vsim", "vsim"],
#        "createemptylib" : ["vlib", "vlib"],
#        "compilevhdl"    : ["vcom", "vcom"],
#        "compileverilog" : ["vlog", "vlog"],
        }

# Set sensible default options for the tools
default_flags = {
        "lint methodology" : "ip -goal start",
        "autocheck verify" : "",
        "xcheck verify" : "",
        "covercheck verify" : "",
        "rdc generate report" : "-resetcheck",
        "cdc generate report" : "-clockcheck",
        "formal verify" : "-justify_initial_x -auto_constraint_off",
        }

coverage_goal = {}

def define_steps(framework, steps):
    """
    Define the steps available in the Questa toolchain

    This function is called by the framework to register the steps available
    in this toolchain. The steps are registered in the order they are defined here,
    so this also defines the order of execution

    Each step is defined by a setup function and a run function. The setup
    function generates the script to run the tool, while the run function
    actually runs the tool and parses the results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param steps: the Steps object where the steps will be registered
    :type steps: fvm.steps.Steps
    """
    steps.add_step(framework, 'lint', setup_lint, run_lint)
    steps.add_step(framework, 'friendliness', setup_friendliness, run_friendliness)
    steps.add_step(framework, 'rulecheck', setup_rulecheck, run_rulecheck)
    steps.add_step(framework, 'xverify', setup_xverify, run_xverify)
    steps.add_step(framework, 'reachability', setup_reachability, run_reachability)
    steps.add_step(framework, 'resets', setup_resets, run_resets)
    steps.add_step(framework, 'clocks', setup_clocks, run_clocks)
    steps.add_step(framework, 'prove', setup_prove, run_prove)
    steps.add_post_step(framework, 'prove', 'formalcover',
                        setup_prove_formalcover, run_prove_formalcover)
    steps.add_post_step(framework, 'prove', 'simcover', setup_prove_simcover, run_prove_simcover)

def create_f_file(filename, sources):
    """
    Create a .f file with the list of sources
    
    :param filename: the name of the .f file to create
    :type filename: str
    :param sources: the list of sources to include in the .f file
    :type sources: list of str
    """
    with open(filename, "w", encoding='utf-8') as f:
        for src in sources:
            print(src, file=f)

def gencompilescript(framework, filename, path):
    """
    Generate script to compile design sources

    This is used as header for the other scripts, since we need to have
    a compiled netlist in order to do anything

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param filename: the name of the script to create
    :type filename: str
    :param path: the path where to create the script
    :type path: str
    """
    # TODO : we must also compile the Verilog sources, if they exist
    # TODO : we must check for the case of only-verilog designs (no VHDL files)
    # TODO : we must check for the case of only-VHDL designs (no verilog files)
    library_path = f"{framework.outdir}/libraries"
    os.makedirs(library_path, exist_ok=True)

    with open(path + '/' + filename, "w", encoding='utf-8') as f:
        print('onerror exit', file=f)
        ordered_libraries = OrderedDict.fromkeys(framework.libraries_from_vhdl_sources)
        for lib in ordered_libraries:
            lib_dir = f"{library_path}/{lib}"
            print(f'if {{[file exists {lib_dir}]}} {{', file=f)
            print(f'    vdel -lib {lib_dir} -all', file=f)
            print('}', file=f)
            print(f'vlib {framework.get_tool_flags("vlib")} {lib_dir}', file=f)
            print(f'vmap {framework.get_tool_flags("vmap")} {lib} {lib_dir}', file=f)
            lib_sources = [src for src, library in zip(framework.vhdl_sources,
                                                       framework.libraries_from_vhdl_sources)
                                                       if library == lib]
            f_file_path = f'{path}/{lib}_design.f'
            create_f_file(f_file_path, lib_sources)
            print(f'vcom {framework.get_tool_flags("vcom")} -{framework.vhdlstd} '
                  f'-work {lib} -autoorder -f {f_file_path}', file=f)
            print('', file=f)

def run_qverify_step(framework, design, step):
    """
    Run a specific step with the Questa formal toolchain.

    A single function can be reused for multiple steps since the tools
    share the same interface through the qverify command line tool/wrapper

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param design: the name of the design to analyze
    :type design: str
    :param step: the name of the step to run
    :type step: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err)
    :rtype: tuple[str, str, int, int]
    """
    # If called with a specific step, run that specific step
    # TODO : questa code should also register its run functions with the
    # steps class
    path = framework.current_path
    report_path = f'{path}/{step}'
    tool = tools[step][0]
    wrapper = tools[step][1]
    framework.logger.debug(f'Running {tool=} with {wrapper=}')
    cmd = [wrapper, '-c', '-od', report_path, '-do', f'{path}/{step}.do']
    open_gui = False
    cmd_stdout, cmd_stderr = "", ""
    stdout_err, stderr_err = 0, 0

    if framework.guinorun is True :
        framework.logger.info(f'{framework.guinorun=}, will not run {step=} with {tool=}')
        open_gui = True
    else :
        framework.logger.trace(f'command: {" ".join(cmd)=}')
        cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, step, tool, framework.verbose)
        stdout_err += framework.logcheck(cmd_stdout, design, step, tool)
        stderr_err += framework.logcheck(cmd_stderr, design, step, tool)

        if framework.gui :
            open_gui = True
    # TODO : maybe run the GUI processes without blocking
    # the rest of the steps? For that we would probably
    # need to pass another option to run_cmd
    if open_gui:
        framework.logger.info(f'{step=}, {tool=}, opening results with GUI')
        db_file = f'{report_path}/{tool}.db'
        cmd = [wrapper, db_file]
        if not os.path.exists(db_file):
            framework.logger.error(f"The database file does not exist: {db_file}")
        else:
            framework.logger.trace(f'command: {" ".join(cmd)=}')
            aux_cmd_stdout, aux_cmd_stderr = framework.run_cmd(cmd, design, step, tool, framework.verbose)
            stdout_err += framework.logcheck(aux_cmd_stdout, design, step, tool)
            stderr_err += framework.logcheck(aux_cmd_stderr, design, step, tool)
            cmd_stdout += aux_cmd_stdout
            cmd_stderr += aux_cmd_stderr

    return cmd_stdout, cmd_stderr, stdout_err, stderr_err

def get_linecheck_common():
    """
    Common patterns for linecheck in all Questa steps

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    return {
        "ignore": [
            "Errors: 0",
            "Error (0)",
            "Warning (0)",
        ],
        "error": ["error", "fatal", "errors"],
        "warning": ["warning", "warnings"],
        "success": [],
    }

def setup_lint(framework, path):
    """
    Generate script to run Lint

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "lint.do"
    gencompilescript(framework, filename, path)
    with open(f'{path}/{filename}', "a", encoding='utf-8') as f:
        print(f'lint methodology {framework.get_tool_flags("lint methodology")}', file=f)
        print(f'lint run -d {framework.current_toplevel} {framework.get_tool_flags("lint run")} '
              f'{framework.generic_args}', file=f)
        print('exit', file=f)

def run_lint(framework, path):
    """
    Run Lint and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the lint directory
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, 'lint')
    lint_rpt_path = f'{path}/lint/lint.rpt'
    if os.path.exists(lint_rpt_path):
        lint_summary = parse_lint.parse_check_summary(lint_rpt_path)
        framework.results[framework.current_toplevel]['lint']['summary'] = lint_summary
        tables.show_step_summary(framework.results[framework.current_toplevel]['lint']['summary'],
                                 "Error", "Warning",
                                 outdir=f'{framework.outdir}/{framework.current_toplevel}/lint',
                                 step="lint")
        if framework.results[framework.current_toplevel]['lint']['summary'].get('Error', {}).get('count', 0) > 0:
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_lint():
    """
    Common patterns for linecheck in the Questa lint step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    return patterns

def setup_friendliness(framework, path):
    """
    Generate script to compile AutoCheck, which also generates a report we
    analyze to determine the design's formal-friendliness

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "friendliness.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        print(f'autocheck compile {framework.get_tool_flags("autocheck compile")} -d '
              f'{framework.current_toplevel} {framework.generic_args}', file=f)
        print('exit', file=f)

def run_friendliness(framework, path):
    """
    Run AutoCheck to generate a friendliness report and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the friendliness directory
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework,
                                                   framework.current_toplevel,
                                                   'friendliness')
    rpt = os.path.join(path, 'friendliness', 'autocheck_design.rpt')
    if os.path.exists(rpt):
        data = parse_design_rpt.data_from_design_summary(rpt)
        score = parse_design_rpt.friendliness_score(data)
        framework.results[framework.current_toplevel]['friendliness']['data'] = data
        framework.results[framework.current_toplevel]['friendliness']['score'] = score
        tables.show_friendliness_score(score,
                                       outdir=f'{framework.outdir}/{framework.current_toplevel}/friendliness',
                                       step="friendliness")

    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_friendliness():
    """Common patterns for linecheck in the Questa friendliness step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    return patterns

def setup_rulecheck(framework, path):
    """
    Generate script to run AutoCheck

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "rulecheck.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        print('autocheck report inconclusives', file=f)
        for line in framework.init_reset:
            print(line, file=f)
        print(f'autocheck compile {framework.get_tool_flags("autocheck compile")} -d '
              f'{framework.current_toplevel} {framework.generic_args}', file=f)
        print(f'autocheck verify {default_flags["autocheck verify"]}', file=f)
        print('exit', file=f)

def run_rulecheck(framework, path):
    """
    Run the rulecheck step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    step = 'rulecheck'
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework,
                                                   framework.current_toplevel,
                                                   step)
    rpt_path = f'{path}/{step}/autocheck_verify.rpt'
    if os.path.exists(rpt_path):
        res = parse_rulecheck.group_by_severity(parse_rulecheck.parse_type_and_severity(rpt_path))
        framework.results[framework.current_toplevel][step]['summary'] = res
        tables.show_step_summary(res,
                                 "Violation", "Caution", "Inconclusive",
                                 outdir=f'{framework.outdir}/{framework.current_toplevel}/{step}',
                                 step=step)
        if framework.results[framework.current_toplevel]['rulecheck']['summary'].get('Violation', {}).get('count', 0) > 0:
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_rulecheck():
    """
    Common patterns for linecheck in the Questa rulecheck step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += [
        "Check                     Evaluations         Found Inconclusives        Waived"
        ]
    patterns["error"] += ["violation", "violations"]
    patterns["warning"] += ["caution", "cautions", "inconclusive", "inconclusives"]
    return patterns

def setup_xverify(framework, path):
    """
    Generate script to run X-Check

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "xverify.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        for line in framework.init_reset:
            print(line, file=f)
        print(f'xcheck compile {framework.get_tool_flags("xcheck compile")} -d '
              f'{framework.current_toplevel} {framework.generic_args}', file=f)
        print(f'xcheck verify {framework.get_tool_flags("xcheck verify")}', file=f)
        print('exit', file=f)

def run_xverify(framework, path):
    """
    Run the xverify step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    step = 'xverify'
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, step)
    rpt_path = f'{path}/{step}/xcheck_verify.rpt'
    if os.path.exists(rpt_path):
        res = parse_xverify.group_by_result(parse_xverify.parse_type_and_result(rpt_path))
        framework.results[framework.current_toplevel][step]['summary'] = res
        tables.show_step_summary(framework.results[framework.current_toplevel][step]['summary'],
                                 "Corruptible", "Incorruptible", "Inconclusive",
                                 outdir=f'{framework.outdir}/{framework.current_toplevel}/{step}',
                                 step=step)
        if framework.results[framework.current_toplevel]['xverify']['summary'].get('Corruptible', {}).get('count', 0) > 0:
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_xverify():
    """
    Common patterns for linecheck in the Questa xverify step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += [
        "Check                    Active     Corruptible   Incorruptible    Inconclusive"
        ]
    patterns["error"] += ["corruptible", "corruptibles"]
    patterns["warning"] += ["incorruptible", "incorruptibles", "inconclusive", "inconclusives"]
    return patterns

def setup_reachability(framework, path):
    """
    Generate a script to run CoverCheck

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "reachability.do"
    # TODO : if a .ucdb file is specified as argument, run the post-simulation
    # analysis instead of the pre-simulation analysis (see
    # https://git.woden.us.es/eda/fvm/-/issues/37#note_4252)
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        for line in framework.init_reset:
            print(line, file=f)
        print(f'covercheck compile {framework.get_tool_flags("covercheck compile")} -d '
              f'{framework.current_toplevel} {framework.generic_args}', file=f)
        # if .ucdb file is specified:
        #    print('covercheck load ucdb {ucdb_file}', file=f)
        #    print(f'covercheck verify -covered_items', file=f)
        print(f'covercheck verify {framework.get_tool_flags("covercheck verify")}', file=f)
        print('exit', file=f)

def run_reachability(framework, path):
    """
    Run the reachability step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    step = 'reachability'
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, step)
    rpt_path = f'{path}/{step}/covercheck_verify.rpt'
    html_path = f'{path}/{step}/reachability.html'
    if os.path.exists(rpt_path):
        parse_reports.parse_reachability_report_to_html(rpt_path, html_path)
        reachability_html = html_path
    else:
        reachability_html = None
    if reachability_html is not None:
        with open(reachability_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        table = parse_reachability.parse_single_table(html_content)
        # Default goal is 90% if not specified otherwise
        goal = coverage_goal.get(step, 90.0)
        res = parse_reachability.unified_format_table(parse_reachability.add_total_row(table),
                                                      goal=goal)
        framework.results[framework.current_toplevel]['reachability']['summary'] = res
        title = f"Reachability Summary for Design: {framework.current_toplevel}"
        tables.show_coverage_summary(res, title=title,
                                    outdir=f'{framework.outdir}/{framework.current_toplevel}/{step}',
                                    step=step)
        if any(row.get("Status") == "fail" for row in framework.results[framework.current_toplevel]['reachability']['summary']):
            status = "goal_not_met"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_reachability():
    """
    Common patterns for linecheck in the Questa reachability step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += [
        "Coverage Type           Active        Witness   Inconclusive    Unreachable"
        ]
    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def gen_reset_config(framework, filename, path):
    """
    Generate reset configuration in the given script
    
    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param filename: the name of the script to append the configuration to
    :type filename: str
    :param path: the path where the script is located
    :type path: str
    """
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        # Clock trees can be both active high and low when some logic is
        # reset when the reset is high and other logic is reset when it is
        # low.
        # Also, reset signals can drive trees of both synchronous and
        # asynchronous resets
        for reset in framework.resets:
            if reset["design"] in (framework.current_toplevel, '*'):
                string = f'netlist reset {reset["name"]}'
                if reset["module"] is not None:
                    string += f' -module {reset["module"]}'
                if reset["group"] is not None:
                    string += f' -group {reset["group"]}'
                if reset["active_low"] is True:
                    string += ' -active_low'
                if reset["active_high"] is True:
                    string += ' -active_high'
                if reset["asynchronous"] is True:
                    string += ' -async'
                if reset["synchronous"] is True:
                    string += ' -sync'
                if reset["external"] is True:
                    string += ' -virtual'
                if reset["remove"] is True:
                    string += ' -remove'
                if reset["ignore"] is True:
                    string += ' -ignore'
                print(string, file=f)

def gen_reset_domain_config(framework, filename, path):
    """
    Generate reset domain configuration in the given script

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param filename: the name of the script to append the configuration to
    :type filename: str
    :param path: the path where the script is located
    :type path: str
    """
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        for domain in framework.reset_domains:
            if domain["design"] in (framework.current_toplevel, '*'):
                for signal in domain["port_list"]:
                    string = f'netlist port resetdomain {signal}'
                    if domain["name"] is not None:
                        string += f' -reset {domain["name"]}'
                    if domain["asynchronous"] is True:
                        string += ' -async'
                    if domain["synchronous"] is True:
                        string += ' -sync'
                    if domain["active_high"] is True:
                        string += ' -active_high'
                    if domain["active_low"] is True:
                        string += ' -active_low'
                    if domain["is_set"] is True:
                        string += ' -set'
                    if domain["no_reset"] is True:
                        string += ' -no_reset'
                    if domain["module"] is not None:
                        string += f' -module {domain["module"]}'
                    if domain["ignore"] is True:
                        string += ' -ignore}'
                    string += ' -add'
                    print(string, file=f)

def gen_clock_config(framework, filename, path):
    """
    Generate clock configuration in the given script

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param filename: the name of the script to append the configuration to
    :type filename: str
    :param path: the path where the script is located
    :type path: str
    """
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        for clock in framework.clocks:
            if clock["design"] in (framework.current_toplevel, '*'):
                string = f'netlist clock {clock["name"]}'
                if clock["module"] is not None:
                    string += f' -module {clock["module"]}'
                if clock["group"] is not None:
                    string += f' -group {clock["group"]} -add'
                if clock["period"] is not None:
                    string += f' -period {clock["period"]}'
                if clock["waveform"] is not None:
                    rise, fall = clock["waveform"]
                    string += f' -waveform {rise} {fall}'
                if clock["external"] is True:
                    string += ' -virtual'
                if clock["remove"] is True:
                    string += ' -remove'
                if clock["ignore"] is True:
                    string += ' -ignore'
                print(string, file=f)

def gen_clock_domain_config(framework, filename, path):
    """
    Generate clock domain configuration in the given script
    
    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param filename: the name of the script to append the configuration to
    :type filename: str
    :param path: the path where the script is located
    :type path: str
    """
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        for domain in framework.clock_domains:
            if domain["design"] in (framework.current_toplevel, '*'):
                for signal in domain["port_list"]:
                    string = f'netlist port domain {signal}'
                    if domain["clock_name"] is not None:
                        string += f' -clock {domain["clock_name"]} -add'
                    if domain["asynchronous"] is True:
                        string += ' -async'
                    if domain["ignore"] is True:
                        string += ' -ignore'
                    if domain["posedge"] is True:
                        string += ' -posedge'
                    if domain["negedge"] is True:
                        string += ' -negedge'
                    if domain["module"] is not None:
                        string += f' -module {domain["module"]}'
                    if domain["inout_clock_in"] is True:
                        string += ' -inout_clock_in'
                    if domain["inout_clock_out"] is True:
                        string += ' -inout_clock_out'
                    print(string, file=f)

def setup_resets(framework, path):
    """
    Generate script to run Reset Domain Crossing

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "resets.do"
    # We first write the header to compile the netlist and then append
    # (mode "a") the tool-specific instructions
    gencompilescript(framework, filename, path)
    gen_clock_config(framework, filename, path)
    gen_clock_domain_config(framework, filename, path)
    gen_reset_config(framework, filename, path)
    gen_reset_domain_config(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        print(f'rdc run -d {framework.current_toplevel} {framework.get_tool_flags("rdc run")} '
              f'{framework.generic_args}', file=f)
        print(f'rdc generate report reset_report.rpt '
              f'{framework.get_tool_flags("rdc generate report")};', file=f)
        print('rdc generate tree -reset reset_tree.rpt;', file=f)
        print('exit', file=f)

def run_resets(framework, path):
    """
    Run the resets step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, 'resets')
    rpt_path = f'{path}/resets/rdc.rpt'
    if os.path.exists(rpt_path):
        res = parse_resets.parse_resets_results(rpt_path)
        framework.results[framework.current_toplevel]['resets']['summary'] = res
        tables.show_step_summary(res,
                                 "Violation", "Caution",
                                 outdir=f'{framework.outdir}/{framework.current_toplevel}/resets',
                                 step="resets")
        if framework.results[framework.current_toplevel]['resets']['summary'].get('Violation', {}).get('count', 0) > 0:
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_resets():
    """
    Common patterns for linecheck in the Questa resets step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def setup_clocks(framework, path):
    """
    Generate script to run Clock Domain Crossing
    
    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "clocks.do"
    # We first write the header to compile the netlist  and then append
    # (mode "a") the tool-specific instructions
    gencompilescript(framework, filename, path)
    gen_clock_config(framework, filename, path)
    gen_clock_domain_config(framework, filename, path)
    gen_reset_config(framework, filename, path)
    gen_reset_domain_config(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        # TODO : also look at reconvergence, and other warnings detected
        #print('netlist clock clk -period 50', file=f)

        # Enable reconvergence to remove warning [hdl-271]
        # TODO : add option to disable reconvergence?
        print('cdc reconvergence on', file=f)
        print(f'cdc run -d {framework.current_toplevel} {framework.get_tool_flags("cdc run")} '
              f'{framework.generic_args}', file=f)
        print(f'cdc generate report clock_report.rpt '
              f'{framework.get_tool_flags("cdc generate report")}', file=f)
        print('cdc generate tree -clock clock_tree.rpt;', file=f)
        print('exit', file=f)

def run_clocks(framework, path):
    """
    Run the clocks step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, 'clocks')
    clocks_rpt_path = f'{path}/clocks/cdc.rpt'
    if os.path.exists(clocks_rpt_path):
        res = parse_clocks.parse_clocks_results(clocks_rpt_path)
        framework.results[framework.current_toplevel]['clocks']['summary'] = res
        tables.show_step_summary(res,
                                 "Violations", "Cautions", proven="Proven",
                                 outdir=f'{framework.outdir}/{framework.current_toplevel}/clocks',
                                 step="clocks")
        if framework.results[framework.current_toplevel]['clocks']['summary'].get('Violations', {}).get('count', 0) > 0:
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_clocks():
    """
    Common patterns for linecheck in the Questa clocks step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Proven (0)"]
    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def setup_prove(framework, path):
    """
    Generate script to run PropCheck
    
    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "prove.do"
    # TODO : can we also compile the PSL files using a .f file?
    gencompilescript(framework, filename, path)
    # Only add the clocks since we don't want to add any extra constraint
    # Also, adding the clock domain make propcheck throw errors because
    # output ports in the clock domain cannot be constrained
    gen_clock_config(framework, filename, path)
    with open(path+'/'+filename, "a", encoding='utf-8') as f:
        print('', file=f)
        print('## Run PropCheck', file=f)
        #print('log_info "***** Running formal compile (compiling formal model)..."', file=f)
        for line in framework.init_reset:
            print(line, file=f)

        for blackbox in framework.blackboxes:
            bb_design, bb_entity = blackbox.split('.', 1)
            if bb_design in (framework.current_toplevel, '*'):
                print(f'netlist blackbox {bb_entity}', file=f)

        for blackbox_instance in framework.blackbox_instances:
            bb_design, bb_instance = blackbox_instance.split('.', 1)
            if bb_design in (framework.current_toplevel, '*'):
                print(f'netlist blackbox instance {bb_instance}', file=f)

        for cutpoint in framework.cutpoints:
            if cutpoint["design"] in (framework.current_toplevel, '*'):
                string = f'netlist cutpoint {cutpoint["signal"]}'
                if cutpoint["module"] is not None:
                    string += f' -module {cutpoint["module"]}'
                if cutpoint["resetval"] is True:
                    string += ' -reset_value'
                if cutpoint["condition"] is not None:
                    string += f'-cond {cutpoint["condition"]}'
                if cutpoint["driver"] is not None:
                    string += f'-driver {cutpoint["driver"]}'
                if cutpoint["wildcards_dont_match_hierarchy_separators"] is True:
                    string += '-match_local_scope'
                print(string, file=f)

        print('formal compile ', end='', file=f)
        print(f'-d {framework.current_toplevel} {framework.generic_args} ', end='', file=f)
        for i in framework.psl_sources :
            print(f'-pslfile {i} ', end='', file=f)
        for i in framework.drom_generated_psl :
            print(f'-pslfile {i} ', end='', file=f)
        print('-include_code_cov ', end='', file=f)
        print(f'{framework.get_tool_flags("formal compile")}', file=f)

        #print('log_info "***** Running formal verify (model checking)..."', file=f)
        # If -cov_mode is specified without arguments, it calculates
        # observability coverage
        print('formal coverage enable -code sbceft', file=f)
        print(f'formal verify {framework.get_tool_flags("formal verify")} -cov_mode', file=f)
        print('', file=f)
        print('## Compute Formal Coverage', file=f)
        print(f'formal generate testbenches '
              f'{framework.get_tool_flags("formal generate testbenches")}',file=f)
        print('formal generate waveforms', file=f)
        print('formal generate waveforms -vcd', file=f)
        print('formal generate report', file=f)
        print('', file=f)
        print('exit', file=f)

def run_prove(framework, path):
    """
    Run the prove step and parse results
    
    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework, framework.current_toplevel, 'prove')
    rpt_path = f'{path}/prove/formal_verify.rpt'
    if os.path.exists(rpt_path):
        res = parse_prove.property_summary(rpt_path)
        framework.results[framework.current_toplevel]['prove']['summary'] = res
        properties = parse_prove.normalize_sections(parse_prove.parse_targets_report(rpt_path))
        tables.show_prove_summary(properties,
                                  outdir=f'{framework.outdir}/{framework.current_toplevel}/prove',
                                  step='prove')
        if (framework.results[framework.current_toplevel]['prove']['summary'].get("Asserts", {}).get("Children", {}).get("Fired", {}).get("Count", 0 )> 0
            or framework.results[framework.current_toplevel]['prove']['summary'].get("Covers", {}).get("Children", {}).get("Uncoverable", {}).get("Count", 0) > 0):
            status = "fail"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_prove():
    """
    Common patterns for linecheck in the Questa prove step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["error"] += ["fired", "uncoverable"]
    # inconclusive only if not in "Proven:" line"
    patterns["warning"] += ["inconclusives", "vacuous", r"^(?!Proven:).*inconclusive"]
    patterns["success"] += ["covered", "proven"]

    return patterns

def setup_prove_simcover(framework, path):
    """
    Modify the replay.vsim.do files to dump UCDB files and waveforms

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    replay_files = glob.glob(path + '/prove/qsim_tb/*/replay.vsim.do')
    for file in replay_files:
        # Modify the replay.vsim.do so:
        #   - It dumps the waveforms into a .vcd file
        #   - It specifies a unique test name so we don't get errors when
        #     merging the UCDBs, and
        #   - It saves a UCDB file
        vcdfilename = os.path.basename(os.path.dirname(file)) + '.vcd'
        helpers.insert_line_after_target(file, "onerror {resume}", f'vcd dumpports -file {vcdfilename} -in -out *')
        helpers.insert_line_before_target(file, "quit -f;", f'coverage attribute -name TESTNAME -value {pathlib.Path(file).parent.name}')
        helpers.insert_line_before_target(file, "quit -f;", "coverage save sim.ucdb")

def run_prove_simcover(framework, path):
    """
    Run the prove.simcover step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    sum_cmd_stdout, sum_cmd_stderr = '', ''
    stdout_err, stderr_err = 0, 0
    replay_files = glob.glob(path + '/prove/qsim_tb/*/replay.vsim.do')
    framework.logger.trace(f'{replay_files=}')
    ucdb_files = []
    elapsed_time = 0
    timestamp = None
    design = framework.current_toplevel

    # Function to run a command in prove.simcover, updating
    # the relevant variables. Used to avoid code duplication
    def simcover_run(tool):
        nonlocal timestamp, elapsed_time, stdout_err, stderr_err, sum_cmd_stdout, sum_cmd_stderr
        cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, 'prove.simcover',
                                                tool, framework.verbose, path)
        elapsed_time += framework.results[design]['prove.simcover']['elapsed_time']
        if timestamp is None:
            timestamp = framework.results[design]['prove.simcover']['timestamp']

        stdout_err += framework.logcheck(cmd_stdout, design, 'prove.simcover', tool)
        stderr_err += framework.logcheck(cmd_stderr, design, 'prove.simcover', tool)

        sum_cmd_stdout += cmd_stdout
        sum_cmd_stderr += cmd_stderr
        framework.results[design]['prove.simcover']['timestamp'] = timestamp
        framework.results[design]['prove.simcover']['elapsed_time'] = elapsed_time

    # Run all the simulations to generate the UCDB files
    for file in replay_files:
        path = pathlib.Path(file).parent
        cmd = ['./replay.scr']
        simcover_run('vsim')
        ucdb_files.append(f'{path}/sim.ucdb')

    # If we have any UCDB files, merge them and generate reports
    if any(os.path.exists(f) for f in ucdb_files):
        # Merge all simulation code coverage files
        path = None
        simcover_path = f"{framework.outdir}/{framework.current_toplevel}/prove.simcover"
        os.makedirs(simcover_path, exist_ok=True)
        cmd = ['vcover', 'merge', '-out', f'{simcover_path}/simcover.ucdb']
        cmd = cmd + ucdb_files
        simcover_run('vcover merge')

        path = simcover_path
        # Generate reports only if the merge was successful
        if os.path.exists(f'{path}/simcover.ucdb'):
            # Generate a csv coverage report
            cmd = ['vcover', 'report', '-csv', '-hierarchical', 'simcover.ucdb',
                '-output', 'simulation_coverage.log']
            simcover_run('vcover report')

            # Generate an html coverage report
            cmd = ['vcover', 'report', '-html', '-annotate', '-details',
                '-testdetails', '-codeAll', '-multibitverbose', '-out',
                'simcover', 'simcover.ucdb']
            simcover_run('vcover report')

    # Generate summary table
    coverage_path = f'{path}/simulation_coverage.log'
    if os.path.exists(coverage_path):
        coverage_data = parse_simcover.parse_coverage_report(coverage_path)
        # Default goal is 90% if not specified otherwise
        goal = coverage_goal.get("prove.simcover", 90.0)
        res = parse_simcover.unified_format_table(parse_simcover.sum_coverage_data(coverage_data),
                                                  goal=goal)
        framework.results[design]['prove.simcover']['summary'] = res
        title = f"Simulation Coverage Summary for Design: {framework.current_toplevel}"
        tables.show_coverage_summary(framework.results[design]['prove.simcover']['summary'],
                                     title=title,
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/prove.simcover',
                                     step='prove.simcover')
        if any(row.get("Status") == "fail" for row in framework.results[framework.current_toplevel]['prove.simcover']['summary']):
            status = "goal_not_met"
    return sum_cmd_stdout, sum_cmd_stderr, stdout_err, stderr_err, status

def get_linecheck_prove_simcover():
    """
    Common patterns for linecheck in the Questa prove.simcover step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """

    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += [
        "Note: (vsim-12126) Error and warning message counts have been restored"
        ]
    patterns["warning"] += ["inconclusive", "inconclusives"]

    return patterns

def setup_prove_formalcover(framework, path):
    """
    Generate script to run formal coverage after prove

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str
    """
    filename = "prove.formalcover.do"
    property_summary = parse_prove.parse_property_summary(f'{path}/prove/prove.log')
    inconclusives = property_summary.get('Assertions', {}).get('Inconclusive', 0)
    with open(f"{path}/{filename}", "w", encoding='utf-8') as f:
        print('onerror exit', file=f)
        print(f"formal load db {path}/prove/propcheck.db",file=f)
        if not framework.is_disabled('observability'):
            print('formal generate coverage -detail_all -cov_mode o', file=f)
        if not framework.is_disabled('reachability'):
            print(f'formal verify {framework.get_tool_flags("formal verify")} '
                  f'-cov_mode reachability', file=f)
            print('formal generate coverage -detail_all -cov_mode r', file=f)
        if not framework.is_disabled('bounded_reachability') and inconclusives != 0:
            print(f'formal verify {framework.get_tool_flags("formal verify")} '
                  f'-cov_mode bounded_reachability', file=f)
            print('formal generate coverage -detail_all -cov_mode b', file=f)
        if not framework.is_disabled('signoff'):
            print(f'formal verify {framework.get_tool_flags("formal verify")} '
                  f'-cov_mode signoff', file=f)
            print('formal generate coverage -detail_all -cov_mode s', file=f)
        print('', file=f)
        print('exit', file=f)

def run_prove_formalcover(framework, path):
    """
    Run the prove.formalcover step and parse results

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param path: the path where to create the script
    :type path: str

    :return: A tuple (cmd_stdout, cmd_stderr, stdout_err, stderr_err, status)
    :rtype: tuple[str, str, int, int, str]
    """
    status = "pass"
    run_stdout, run_stderr, stdout_err, stderr_err = run_qverify_step(framework,
                                                                      framework.current_toplevel,
                                                                      'prove.formalcover')

    # Copy the database to the prove folder so we can
    # see coverage results in prove guinorun mode
    tool = tools["prove"][0]
    db_dir = f'{path}/prove.formalcover/{tool}.db'
    if os.path.exists(db_dir):
        shutil.copytree(db_dir, f'{path}/prove/{tool}.db', dirs_exist_ok=True)

    report_path = path + '/prove.formalcover'
    # Generate HTML reports
    rpt_path = f'{report_path}/formal_observability.rpt'
    html_path = f'{report_path}/formal_observability.html'
    if os.path.exists(rpt_path):
        parse_reports.parse_formal_observability_report_to_html(rpt_path,
                                                                html_path)
    rpt_path = f'{report_path}/formal_reachability.rpt'
    html_path = f'{report_path}/formal_reachability.html'
    if os.path.exists(rpt_path):
        parse_reports.parse_formal_reachability_report_to_html(rpt_path,
                                                                html_path)
    rpt_path = f'{report_path}/formal_signoff.rpt'
    html_path = f'{report_path}/formal_signoff.html'
    if os.path.exists(rpt_path):
        parse_reports.parse_formal_signoff_report_to_html(rpt_path, html_path)
        formal_signoff_html = html_path
    else:
        formal_signoff_html = None

    if formal_signoff_html is not None:
        with open(formal_signoff_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Generate the result table
        table = parse_formal_signoff.parse_coverage_table(html_content)
        filtered_tables = parse_formal_signoff.filter_coverage_tables(table)

        if filtered_tables:
            # Default goal is 90% if not specified otherwise
            goal = coverage_goal.get("prove.formalcover", 90.0)
            res = parse_formal_signoff.unified_format_table(
                parse_formal_signoff.add_total_field(filtered_tables[0]),
                goal=goal)
            framework.results[framework.current_toplevel]['prove.formalcover']['summary'] = res

            title = f"Formal Signoff Coverage Summary for Design: {framework.current_toplevel}"
            tables.show_coverage_summary(res,
                                            title=title,
                                            outdir=f'{framework.outdir}/{framework.current_toplevel}/prove.formalcover',
                                            step='prove.formalcover')
            if any(row.get("Status") == "fail" for row in framework.results[framework.current_toplevel]['prove.formalcover']['summary']):
                status = "goal_not_met"
    return run_stdout, run_stderr, stdout_err, stderr_err, status

def get_linecheck_prove_formalcover():
    """
    Common patterns for linecheck in the Questa prove.formalcover step

    :return: A dictionary containing linecheck patterns
    :rtype: dict[str, list[str]]
    """
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += [
        "Cover Type               Total    Unreachable   Inconclusive      Reachable"
        ]
    patterns["warning"] += ["inconclusive", "inconclusives"]

    return patterns

def set_timeout(framework, step, timeout):
    """
    Set the timeout for a specific step

    The timeout should be provided as a string combining a number and a unit:

    - ``s`` for seconds (e.g., "1s")
    - ``m`` for minutes (e.g., "10m")
    - ``h`` for hours (e.g., "1h")
    - ``d`` for days (e.g., "2d")

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param step: the step to set the timeout for. One of "rulecheck",
                 "xverify", "reachability", "prove"
    :type step: str
    :param timeout: Timeout value as a string with a number and unit.
    :type timeout: str
    """
    timeout_value = f" -timeout {timeout} "
    if step == "rulecheck":
        framework.tool_flags["autocheck verify"] += timeout_value
    elif step == "xverify":
        framework.tool_flags["xcheck verify"] += timeout_value
    elif step == "reachability":
        framework.tool_flags["covercheck verify"] += timeout_value
    elif step == "prove":
        framework.tool_flags["formal verify"] += timeout_value

def set_coverage_goal(step, goal):
    """
    Set the coverage goal for a specific step
    
    :param step: the step to set the coverage goal for
    :type step: str
    :param goal: Coverage goal value, must be between 0 and 100
    :type goal: int or float
    """
    coverage_goal[step] = goal

def generics_to_args(generics):
    """
    Converts a dict with generic:value pairs to the argument we have to
    pass to the tools

    :param generics: A dictionary with generic names as keys and their values
                     as values
    :type generics: dict[str, str]

    :return: A string with the generics formatted as tool arguments
    :rtype: str
    """
    string = ''
    for i in generics:
        string += f'-g {i}={generics[i]} '
    return string

def formal_initialize_reset(framework, reset, active_high=True, cycles=1):
    """
    Initialize reset for formal steps.

    :param framework: the FVMFramework object
    :type framework: fvm.framework.FVMFramework
    :param reset: the name of the reset signal
    :type reset: str
    :param active_high: True if the reset is active high, False if it is
                        active low. Defaults to True.
    :type active_high: bool
    :param cycles: number of cycles to keep the reset active at the start
                   of the formal analysis
    :type cycles: int
    """
    if active_high:
        line = f'formal init {{{reset}=1;##{cycles+1};{reset}=0}}'
        framework.init_reset.append(line)
    else:
        line = f'formal init {{{reset}=0;##{cycles+1};{reset}=1}}'
        framework.init_reset.append(line)
