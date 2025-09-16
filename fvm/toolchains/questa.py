# Questa toolchain definition

import os
from collections import OrderedDict
from datetime import datetime
import shutil
import glob
import pathlib
import time

from rich.console import Console
from rich.table import Table
from rich.text import Text

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
from fvm import generate_test_cases
from fvm import helpers
from fvm.toolchains import toolchains

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

def define_steps(steps):
    steps.add_step('lint', setup_lint, run_lint)
    steps.add_step('friendliness', setup_friendliness, run_friendliness)
    steps.add_step('rulecheck', setup_rulecheck, run_rulecheck)
    steps.add_step('xverify', setup_xverify, run_xverify)
    steps.add_step('reachability', setup_reachability, run_reachability)
    steps.add_step('resets', setup_resets, run_resets)
    steps.add_step('clocks', setup_clocks, run_clocks)
    steps.add_step('prove', setup_prove, run_prove)
    steps.add_post_step('prove', 'formalcover', setup_prove_formalcover, run_prove_formalcover)
    steps.add_post_step('prove', 'simcover', setup_prove_simcover, run_prove_simcover)

def create_f_file(filename, sources):
    with open(filename, "w") as f:
        for src in sources:
            print(src, file=f)

# TODO : probably all these functions do not need to receive path as argument
# and can instead use framework.current_path, but we have to make sure that the
# fvmframework is correctly setting the path (it should be!)

def gencompilescript(framework, filename, path):
    """Generate script to compile design sources"""
    # TODO : we must also compile the Verilog sources, if they exist
    # TODO : we must check for the case of only-verilog designs (no VHDL files)
    # TODO : we must check for the case of only-VHDL designs (no verilog files)
    # TODO : libraries folder should be inside fvm_out as per #268
    library_path = f"{framework.outdir}/libraries"
    os.makedirs(library_path, exist_ok=True)

    # TODO : probably the following call to create_f_file is not needed
    #create_f_file(f'{path}/design.f', framework.vhdl_sources)

    """ This is used as header for the other scripts, since we need to have
    a compiled netlist in order to do anything"""
    with open(path + '/' + filename, "w") as f:
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
                                                       framework.libraries_from_vhdl_sources) if library == lib]
            f_file_path = f'{path}/{lib}_design.f'
            create_f_file(f_file_path, lib_sources)
            print(f'vcom {framework.get_tool_flags("vcom")} -{framework.vhdlstd} -work {lib} -autoorder -f {f_file_path}', file=f)
            print('', file=f)

# TODO: this function is too big, it can and must be simplified a bit
def run_qverify_step(framework, design, step):
    """Run a specific step with the Questa formal toolchain. A single function
    can be reused for multiple steps since the tools share the same interface
    through the qverify command line tool/wrapper"""
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
    err = False

    if framework.list == True :
        framework.logger.info(f'Available step: {step}. Tool: {tool}, command = {" ".join(cmd)}')
    elif framework.guinorun == True :
        framework.logger.info(f'{framework.guinorun=}, will not run {step=} with {tool=}')
    else :
        framework.logger.trace(f'command: {" ".join(cmd)=}')
        cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, step, tool, framework.verbose)
        stdout_err = framework.logcheck(cmd_stdout, design, step, tool)
        stderr_err = framework.logcheck(cmd_stderr, design, step, tool)

        logfile = f'{report_path}/{step}.log'
        framework.logger.info(f'{step=}, {tool=}, finished, output written to {logfile}')
        with open(logfile, 'w') as f :
            f.write(cmd_stdout)
            f.write(cmd_stderr)
        # We cannot exit here immediately because then we wouldn't
        # be able to open the GUI if there is any error, but we can
        # record the error and propagate it outside the function
        if stdout_err or stderr_err:
            if framework.is_failure_allowed(design, step) == False:
                err = True
        if stdout_err or stderr_err:
            if framework.is_failure_allowed(design, step) == False:
                framework.results[design][step]['status'] = 'fail'
            else:
                framework.results[design][step]['status'] = 'broken'
        else:
            framework.results[design][step]['status'] = 'pass'
        if framework.gui :
            open_gui = True
    if framework.guinorun and framework.list == False :
        open_gui = True
        # TODO : This is provisional because the function returns
        # cmd_stdout and cmd_stderr. It may be ok because in
        # guinorun mode we don't care about those values
        cmd_stdout, cmd_stderr = "", ""
    # TODO : maybe check for errors also in the GUI?
    # TODO : maybe run the GUI processes without blocking
    # the rest of the steps? For that we would probably
    # need to pass another option to run_cmd
    # TODO : code here can be deduplicated by having the database
    # names (.db) in a dictionary -> just open {tool}.db
    if open_gui:
        framework.logger.info(f'{step=}, {tool=}, opening results with GUI')
        db_file = f'{report_path}/{tool}.db'
        cmd = [wrapper, db_file]
        if not os.path.exists(db_file):
            framework.logger.error(f"The database file does not exist: {db_file}")
        else:
            framework.logger.trace(f'command: {" ".join(cmd)=}')
            framework.run_cmd(cmd, design, step, tool, framework.verbose)

    return cmd_stdout, cmd_stderr, err

def get_linecheck_common():
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
    """Generate script to run Lint"""
    print("**** setup lint ****")
    filename = "lint.do"
    gencompilescript(framework, filename, path)
    with open(f'{path}/{filename}', "a") as f:
        print(f'lint methodology {framework.get_tool_flags("lint methodology")}', file=f)
        print(f'lint run -d {framework.current_toplevel} {framework.get_tool_flags("lint run")} {framework.generic_args}', file=f)
        print('exit', file=f)

def run_lint(framework, path):
    print("**** run lint ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'lint')
    lint_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/lint/lint.rpt'
    if os.path.exists(lint_rpt_path):
        framework.results[framework.current_toplevel]['lint']['summary'] = parse_lint.parse_check_summary(lint_rpt_path)
        toolchains.show_step_summary(framework.results[framework.current_toplevel]['lint']['summary'], "Error", "Warning",
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/lint', step="lint")
    return run_stdout, run_stderr, err

def get_linecheck_lint():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    return patterns

def setup_friendliness(framework, path):
    print("**** setup friendliness ****")
    """Generate script to compile AutoCheck, which also generates a report we
    analyze to determine the design's formal-friendliness"""
    filename = "friendliness.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        print(f'autocheck compile {framework.get_tool_flags("autocheck compile")} -d {framework.current_toplevel} {framework.generic_args}', file=f)
        print('exit', file=f)

def run_friendliness(framework, path):
    print("**** run friendliness ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'friendliness')
    rpt = os.path.join(path, 'friendliness', 'autocheck_design.rpt')
    if os.path.exists(rpt):
        data = parse_design_rpt.data_from_design_summary(rpt)
        framework.results[framework.current_toplevel]['friendliness']['data'] = data
        framework.results[framework.current_toplevel]['friendliness']['score'] = parse_design_rpt.friendliness_score(data)
        toolchains.show_friendliness_score(framework.results[framework.current_toplevel]['friendliness']['score'])

    return run_stdout, run_stderr, err

def get_linecheck_friendliness():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    return patterns

def setup_rulecheck(framework, path):
    print("**** setup rulecheck ****")
    """Generate script to run AutoCheck"""
    filename = "rulecheck.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        print(f'autocheck report inconclusives', file=f)
        for line in framework.init_reset:
            print(line, file=f)
        print(f'autocheck compile {framework.get_tool_flags("autocheck compile")} -d {framework.current_toplevel} {framework.generic_args}', file=f)
        print(f'autocheck verify {default_flags["autocheck verify"]}', file=f)
        print('exit', file=f)

def run_rulecheck(framework, path):
    print("**** run rulecheck ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'rulecheck')
    rulecheck_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/rulecheck/autocheck_verify.rpt'
    if os.path.exists(rulecheck_rpt_path):
        framework.results[framework.current_toplevel]['rulecheck']['summary'] = parse_rulecheck.group_by_severity(parse_rulecheck.parse_type_and_severity(rulecheck_rpt_path))
        toolchains.show_step_summary(framework.results[framework.current_toplevel]['rulecheck']['summary'], "Violation", "Caution", "Inconclusive",
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/rulecheck', step="rulecheck")
    return run_stdout, run_stderr, err

def get_linecheck_rulecheck():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Check                     Evaluations         Found Inconclusives        Waived"]
    patterns["error"] += ["violation", "violations"]
    patterns["warning"] += ["caution", "cautions", "inconclusive", "inconclusives"]
    return patterns

def setup_xverify(framework, path):
    print("**** setup xverify ****")
    filename = "xverify.do"
    """Generate script to run X-Check"""
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        for line in framework.init_reset:
            print(line, file=f)
        print(f'xcheck compile {framework.get_tool_flags("xcheck compile")} -d {framework.current_toplevel} {framework.generic_args}', file=f)
        print(f'xcheck verify {framework.get_tool_flags("xcheck verify")}', file=f)
        print('exit', file=f)

def run_xverify(framework, path):
    print("**** run xverify ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'xverify')
    xverify_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/xverify/xcheck_verify.rpt'
    if os.path.exists(xverify_rpt_path):
        framework.results[framework.current_toplevel]['xverify']['summary'] = parse_xverify.group_by_result(parse_xverify.parse_type_and_result(xverify_rpt_path))
        toolchains.show_step_summary(framework.results[framework.current_toplevel]['xverify']['summary'], "Corruptible", "Incorruptible", "Inconclusive",
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/xverify', step="xverify")
    return run_stdout, run_stderr, err

def get_linecheck_xverify():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Check                    Active     Corruptible   Incorruptible    Inconclusive"]
    patterns["error"] += ["corruptible", "corruptibles"]
    patterns["warning"] += ["incorruptible", "incorruptibles", "inconclusive", "inconclusives"]
    return patterns

def setup_reachability(framework, path):
    print("**** setup reachability ****")
    filename = "reachability.do"
    # TODO : if a .ucdb file is specified as argument, run the post-simulation
    # analysis instead of the pre-simulation analysis (see
    # https://git.woden.us.es/eda/fvm/-/issues/37#note_4252)
    """Generate a script to run CoverCheck"""
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        for line in framework.init_reset:
            print(line, file=f)
        print(f'covercheck compile {framework.get_tool_flags("covercheck compile")} -d {framework.current_toplevel} {framework.generic_args}', file=f)
        # if .ucdb file is specified:
        #    print('covercheck load ucdb {ucdb_file}', file=f)
        #    print(f'covercheck verify -covered_items', file=f)
        print(f'covercheck verify {framework.get_tool_flags("covercheck verify")}', file=f)
        print('exit', file=f)

def run_reachability(framework, path):
    print("**** run reachability ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'reachability')
    reachability_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/reachability/covercheck_verify.rpt'
    reachability_html_path = f'{framework.outdir}/{framework.current_toplevel}/reachability/reachability.html'
    if os.path.exists(reachability_rpt_path):
        parse_reports.parse_reachability_report_to_html(reachability_rpt_path, reachability_html_path)
        reachability_html = reachability_html_path
    else:
        reachability_html = None
    if reachability_html is not None:
        with open(reachability_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tables = parse_reachability.parse_single_table(html_content)
        framework.results[framework.current_toplevel]['reachability']['summary'] = parse_reachability.unified_format_table(parse_reachability.add_total_row(tables))
        toolchains.show_coverage_summary(framework.results[framework.current_toplevel]['reachability']['summary'],
                                             title=f"Reachability Summary for Design: {framework.current_toplevel}")
    return run_stdout, run_stderr, err

# TODO : We have to consider if Uncoverable is an error or a warning or nothing.
# If we consider it an error, then reachability will fail in most designs.
# Also, in big designs, if we show these logs, the user won't be able to see
# anything else
def get_linecheck_reachability():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Coverage Type           Active        Witness   Inconclusive    Unreachable"]
    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def gen_reset_config(framework, filename, path):
    with open(path+'/'+filename, "a") as f:
        # TODO : let the user specify clock names, polarities, sync/async,
        # clock domains and reset domains
        # Clock trees can be both active high and low when some logic is
        # reset when the reset is high and other logic is reset when it is
        # low.
        # Also, reset signals can drive trees of both synchronous and
        # asynchronous resets
        for reset in framework.resets:
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
    with open(path+'/'+filename, "a") as f:
        for domain in framework.reset_domains:
            for signal in domain["port_list"]:
                string = f'netlist port resetdomain {signal}'
                string += f' -reset {domain["name"]}'
                if domain["asynchronous"] is True:
                    string += f' -async'
                if domain["synchronous"] is True:
                    string += f' -sync'
                if domain["active_high"] is True:
                    string += f' -active_high'
                if domain["active_low"] is True:
                    string += f' -active_low'
                if domain["is_set"] is True:
                    string += f' -set'
                if domain["no_reset"] is True:
                    string += f' -no_reset'
                if domain["ignore"] is True:
                    string += ' -ignore}'
                string += ' -add'
                print(string, file=f)

def gen_clock_config(framework, filename, path):
    with open(path+'/'+filename, "a") as f:
        for clock in framework.clocks:
            string = f'netlist clock {clock["name"]}'
            if clock["module"] is not None:
                string += f' -module {clock["module"]}'
            if clock["group"] is not None:
                string += f' -group {clock["group"]} -add'
            if clock["period"] is not None:
                string += f' -period {clock["period"]}'
            if clock["waveform"] is not None:
                string += f' -waveform {clock["waveform"]}'
            if clock["external"] is True:
                string += ' -virtual'
            if clock["remove"] is True:
                string += ' -remove'
            if clock["ignore"] is True:
                string += ' -ignore'
            print(string, file=f)

# This is questa-specific
def gen_clock_domain_config(framework, filename, path):
    with open(path+'/'+filename, "a") as f:
        for domain in framework.clock_domains:
            string = f'netlist port domain'
            for signal in domain["port_list"]:
                string += f' {signal}'
            string += f' -clock {domain["name"]} -add'
            if domain["asynchronous"] is True:
                string += ' -async'
            if domain["synchronous"] is True:
                string += ' -sync'
            if domain["ignore"] is True:
                string += ' -ignore'
            if domain["posedge"] is True:
                string += ' -posedge'
            if domain["negedge"] is True:
                string += ' -negedge'
            if domain["module"] is not None:
                string += f' -module {domain["module"]}'
            if domain["inout_clock_in"] is not None:
                string += f' -inout_clock_in {domain["inout_clock_in"]}'
            if domain["inout_clock_out"] is not None:
                string += f' -inout_clock_out {domain["inout_clock_out"]}'
            print(string, file=f)
        #print('netlist reset rst -active_high -async', file=f)
        #print('netlist port domain rst -clock clk', file=f)
        #print('netlist port domain data -clock clk', file=f)
        #print('netlist port domain empty -clock clk', file=f)
        #print('netlist port resetdomain data -reset rst', file=f)
        #print('netlist port resetdomain empty -reset rst', file=f)
        #print('netlist clock clk', file=f)

def setup_resets(framework, path):
    print("**** setup resets ****")
    filename = "resets.do"
    # We first write the header to compile the netlist and then append
    # (mode "a") the tool-specific instructions
    gencompilescript(framework, filename, path)
    gen_clock_config(framework, filename, path)
    gen_clock_domain_config(framework, filename, path)
    gen_reset_config(framework, filename, path)
    gen_reset_domain_config(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        print(f'rdc run -d {framework.current_toplevel} {framework.get_tool_flags("rdc run")} {framework.generic_args}', file=f)
        print(f'rdc generate report reset_report.rpt {framework.get_tool_flags("rdc generate report")};', file=f)
        print('rdc generate tree -reset reset_tree.rpt;', file=f)
        print('exit', file=f)

def run_resets(framework, path):
    print("**** run resets ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'resets')
    resets_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/resets/rdc.rpt'
    if os.path.exists(resets_rpt_path):
        framework.results[framework.current_toplevel]['resets']['summary'] = parse_resets.parse_resets_results(resets_rpt_path)
        toolchains.show_step_summary(framework.results[framework.current_toplevel]['resets']['summary'], "Violation", "Caution",
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/resets', step="resets")
    return run_stdout, run_stderr, err

def get_linecheck_resets():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def setup_clocks(framework, path):
    print("**** setup clocks ****")
    filename = "clocks.do"
    """Generate script to run Clock Domain Crossing"""
    # We first write the header to compile the netlist  and then append
    # (mode "a") the tool-specific instructions
    gencompilescript(framework, filename, path)
    gen_clock_config(framework, filename, path)
    gen_clock_domain_config(framework, filename, path)
    gen_reset_config(framework, filename, path)
    gen_reset_domain_config(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        # TODO : let the user specify clock names, clock domains and reset domains
        # TODO : also look at reconvergence, and other warnings detected
        #print('netlist clock clk -period 50', file=f)

        # Enable reconvergence to remove warning [hdl-271]
        # TODO : add option to disable reconvergence?
        print(f'cdc reconvergence on', file=f)
        print(f'cdc run -d {framework.current_toplevel} {framework.get_tool_flags("cdc run")} {framework.generic_args}', file=f)
        print(f'cdc generate report clock_report.rpt {framework.get_tool_flags("cdc generate report")}', file=f)
        print('cdc generate tree -clock clock_tree.rpt;', file=f)
        print('exit', file=f)

def run_clocks(framework, path):
    print("**** run clocks ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'clocks')
    clocks_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/clocks/cdc.rpt'
    if os.path.exists(clocks_rpt_path):
        framework.results[framework.current_toplevel]['clocks']['summary'] = parse_clocks.parse_clocks_results(clocks_rpt_path)
        toolchains.show_step_summary(framework.results[framework.current_toplevel]['clocks']['summary'], "Violations", "Cautions", proven="Proven",
                                     outdir=f'{framework.outdir}/{framework.current_toplevel}/clocks', step="clocks")
    return run_stdout, run_stderr, err

def get_linecheck_clocks():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Proven (0)"]
    patterns["warning"] += ["inconclusive", "inconclusives"]
    return patterns

def setup_prove(framework, path):
    print("**** setup prove ****")
    filename = "prove.do"
    # TODO : we will need arguments for the clocks, timeout, we probably need
    # to detect compile order if vcom doesn't detect it, set the other options
    # such as timeout... and also throw some errors if any option is not
    # specified. This is not trivial. Also, in the future we may want to
    # specify verilog files with vlog, etc...
    # TODO : can we also compile the PSL files using a .f file?
    """Generate script to run PropCheck"""
    gencompilescript(framework, filename, path)
    # Only add the clocks since we don't want to add any extra constraint
    # Also, adding the clock domain make propcheck throw errors because
    # output ports in the clock domain cannot be constrained
    gen_clock_config(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        print('', file=f)
        print('## Run PropCheck', file=f)
        #print('log_info "***** Running formal compile (compiling formal model)..."', file=f)
        for line in framework.init_reset:
            print(line, file=f)

        for blackbox in framework.blackboxes:
            print(f'netlist blackbox {blackbox}', file=f)

        for blackbox_instance in framework.blackbox_instances:
            print(f'netlist blackbox instance {blackbox_instance}', file=f)

        for cutpoint in framework.cutpoints:
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
        print(f'formal coverage enable -code sbceft', file=f)
        print(f'formal verify {framework.get_tool_flags("formal verify")} -cov_mode', file=f)
        print('', file=f)
        print('## Compute Formal Coverage', file=f)
        #print('log_info "***** Running formal verify to get coverage..."', file=f)
        # TODO : maybe we should run coverage collection in separate
        # scripts so we can better capture if there have been any errors,
        # and also to annotate if they have been skipped
        #print('log_info "***** Running formal generate coverage..."', file=f)
        print(f'formal generate testbenches {framework.get_tool_flags("formal generate testbenches")}', file=f)
        print('formal generate waveforms', file=f)
        print('formal generate waveforms -vcd', file=f)
        print('formal generate report', file=f)
        print('', file=f)
        print('exit', file=f)

def run_prove(framework, path):
    print("**** run prove ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'prove')
    prove_rpt_path = f'{framework.outdir}/{framework.current_toplevel}/prove/formal_verify.rpt'
    if os.path.exists(prove_rpt_path):
        framework.results[framework.current_toplevel]['prove']['summary'] = generate_test_cases.property_summary(prove_rpt_path)
        properties = parse_prove.normalize_sections(parse_prove.parse_targets_report(prove_rpt_path))
        toolchains.show_prove_summary(properties)
    return run_stdout, run_stderr, err

def get_linecheck_prove():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["error"] += ["fired", "uncoverable"]
    patterns["warning"] += ["inconclusives", "vacuous", r"^(?!Proven:).*inconclusive"] # inconclusive only if not in "Proven:" line"
    patterns["success"] += ["covered"]

    return patterns

def setup_prove_simcover(framework, path):
    print("**** setup prove_simcover ****")
    pass

def run_prove_simcover(framework, path):
    print("**** run prove_simcover ****")
    # TODO: check errors in every call instead of summing everything
    # and just checking at the end (hopefully without copying the code
    # in three different places)
    # TODO: try to deduplicate some of the code
    # TODO: append all the logs to the same message so it appears in
    # the reports, and not only the last log (vcover report)
    stdout_err = 0
    stderr_err = 0
    replay_files = glob.glob(framework.outdir+'/'+framework.current_toplevel+'/prove/qsim_tb/*/replay.vsim.do')
    framework.logger.trace(f'{replay_files=}')
    ucdb_files = list()
    elapsed_time = 0
    timestamp = None
    design = framework.current_toplevel
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
        # TODO: Maybe we need to modify the replay.scr so it exports
        # more types of code coverage, we will know that when we try
        # bigger circuits
        # Run the replay script
        path = pathlib.Path(file).parent
        cmd = ['./replay.scr']
        cmd_stdout, cmd_stderr = framework.run_cmd(cmd,
                                                   framework.current_toplevel,
                                                   'prove.simcover', 'vsim',
                                                   framework.verbose, path)
        elapsed_time += framework.results[design]['prove.simcover']['elapsed_time']
        if timestamp is None:
            timestamp = framework.results[design]['prove.simcover']['timestamp']
        # TODO : maybe check for errors here?
        tool = 'vsim'
        stdout_err += framework.logcheck(cmd_stdout, design, 'prove.simcover', tool)
        stderr_err += framework.logcheck(cmd_stderr, design, 'prove.simcover', tool)
        ucdb_files.append(f'{path}/sim.ucdb')
    # Merge all simulation code coverage
    path = None

    simcover_path = f"{framework.outdir}/{framework.current_toplevel}/prove.simcover"
    os.makedirs(simcover_path, exist_ok=True)

    cmd = ['vcover', 'merge', '-out', f'{simcover_path}/simcover.ucdb']
    cmd = cmd + ucdb_files
    framework.logger.info(f'{cmd=}, {path=}')
    cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, 'prove.simcover',
                                               'vcover merge', framework.verbose, path)
    elapsed_time += framework.results[design]['prove.simcover']['elapsed_time']
    if timestamp is None:
        timestamp = framework.results[design]['prove.simcover']['timestamp']
    # TODO : maybe check for errors here?
    tool = 'vcover'
    stdout_err += framework.logcheck(cmd_stdout, design, 'prove.simcover', tool)
    stderr_err += framework.logcheck(cmd_stderr, design, 'prove.simcover', tool)

    # Check for errors
    err = False
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            err = True
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            framework.results[design]['prove.simcover']['status'] = 'fail'
        else:
            framework.results[design]['prove.simcover']['status'] = 'broken'

    # Generate simcover summary
    path = f'{framework.outdir}/{framework.current_toplevel}/prove.simcover'
    cmd = ['vcover', 'report', '-csv', '-hierarchical', 'simcover.ucdb',
           '-output', 'simulation_coverage.log']
    cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, 'prove.simcover',
                                               'vcover report', framework.verbose, path)
    elapsed_time += framework.results[design]['prove.simcover']['elapsed_time']
    framework.results[design]['prove.simcover']['timestamp'] = timestamp
    framework.results[design]['prove.simcover']['elapsed_time'] = elapsed_time
    tool = 'vcover'
    stdout_err += framework.logcheck(cmd_stdout, design, 'prove.simcover', tool)
    stderr_err += framework.logcheck(cmd_stderr, design, 'prove.simcover', tool)

    # Check for errors
    err = False
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            err = True
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            framework.results[design]['prove.simcover']['status'] = 'fail'
        else:
            framework.results[design]['prove.simcover']['status'] = 'broken'
    else:
        framework.results[design]['prove.simcover']['status'] = 'pass'

    # Generate an html report
    path = f'{framework.outdir}/{framework.current_toplevel}/prove.simcover'
    cmd = ['vcover', 'report', '-html', '-annotate', '-details',
           '-testdetails', '-codeAll', '-multibitverbose', '-out',
           'simcover', 'simcover.ucdb']
    cmd_stdout, cmd_stderr = framework.run_cmd(cmd, design, 'prove.simcover',
                                               'vcover report', framework.verbose, path)
    elapsed_time += framework.results[design]['prove.simcover']['elapsed_time']
    framework.results[design]['prove.simcover']['timestamp'] = timestamp
    framework.results[design]['prove.simcover']['elapsed_time'] = elapsed_time
    # TODO : maybe check for errors here?
    tool = 'vcover'
    stdout_err += framework.logcheck(cmd_stdout, design, 'prove.simcover', tool)
    stderr_err += framework.logcheck(cmd_stderr, design, 'prove.simcover', tool)
    # TODO : maybe create also a text report, as #141 suggests?

    # Check for errors
    err = False
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            err = True
    if stdout_err or stderr_err:
        if framework.is_failure_allowed(design, 'prove.simcover') == False:
            framework.results[design]['prove.simcover']['status'] = 'fail'
        else:
            framework.results[design]['prove.simcover']['status'] = 'broken'
    else:
        framework.results[design]['prove.simcover']['status'] = 'pass'

    if framework.results[design]['prove.simcover']['summary'] is not None:
        coverage_data = parse_simcover.parse_coverage_report(f'{path}/simulation_coverage.log')
        framework.results[design]['prove.simcover']['summary'] = parse_simcover.unified_format_table(parse_simcover.sum_coverage_data(coverage_data))
        toolchains.show_coverage_summary(framework.results[design]['prove.simcover']['summary'],
                                             title=f"Simulation Coverage Summary for Design: {framework.current_toplevel}")

    return err

def get_linecheck_prove_simcover():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Note: (vsim-12126) Error and warning message counts have been restored"]
    patterns["warning"] += ["inconclusive", "inconclusives"]

    return patterns

def setup_prove_formalcover(framework, path):
    print("**** setup prove_formalcover ****")
    filename = "prove.formalcover.do"
    property_summary = generate_test_cases.parse_property_summary(f'{path}/prove/prove.log')
    inconclusives = property_summary.get('Assertions', {}).get('Inconclusive', 0)
    with open(f"{path}/{filename}", "a") as f:
        print('onerror exit', file=f)
        print(f"formal load db {path}/prove/propcheck.db",file=f)
        # TODO: Delete is_disabled
        if not framework.is_disabled('observability'):
            print('formal generate coverage -detail_all -cov_mode o', file=f)
        if not framework.is_disabled('reachability'):
            print(f'formal verify {framework.get_tool_flags("formal verify")} -cov_mode reachability', file=f)
            print('formal generate coverage -detail_all -cov_mode r', file=f)
        if not framework.is_disabled('bounded_reachability') and inconclusives != 0:
            print(f'formal verify {framework.get_tool_flags("formal verify")} -cov_mode bounded_reachability', file=f)
            print('formal generate coverage -detail_all -cov_mode b', file=f)
        if not framework.is_disabled('signoff'):
            print(f'formal verify {framework.get_tool_flags("formal verify")} -cov_mode signoff', file=f)
            print('formal generate coverage -detail_all -cov_mode s', file=f)
        print('', file=f)
        print('exit', file=f)

# TODO: Decide what to return. Maybe stdout, stderr, and status?
def run_prove_formalcover(framework, path):
    print("**** run prove_formalcover ****")
    run_stdout, run_stderr, err = run_qverify_step(framework, framework.current_toplevel, 'prove.formalcover')
    report_path = path + '/prove.formalcover'
    if not framework.is_disabled('signoff'):
        formal_signoff_rpt_path = f'{report_path}/formal_signoff.rpt'
        formal_signoff_html_path = f'{report_path}/formal_signoff.html'
        if os.path.exists(formal_signoff_rpt_path):
            parse_reports.parse_formal_signoff_report_to_html(formal_signoff_rpt_path, formal_signoff_html_path)
            formal_signoff_html = formal_signoff_html_path
        else:
            formal_signoff_html = None
        if formal_signoff_html is not None:
            with open(formal_signoff_html, 'r', encoding='utf-8') as f:
                html_content = f.read()

            tables = parse_formal_signoff.parse_coverage_table(html_content)
            filtered_tables = parse_formal_signoff.filter_coverage_tables(tables)

            if filtered_tables:
                framework.results[framework.current_toplevel]['prove.formalcover']['summary'] = parse_formal_signoff.unified_format_table(
                                                parse_formal_signoff.add_total_field(filtered_tables[0]))

                toolchains.show_coverage_summary(framework.results[framework.current_toplevel]['prove.formalcover']['summary'],
                                                    title=f"Formal Coverage Summary for Design: {framework.current_toplevel}")
    return err

def get_linecheck_prove_formalcover():
    patterns = get_linecheck_common()

    # Make a copy to avoid modifying the original dict
    patterns = {k: v.copy() for k, v in patterns.items()}

    patterns["ignore"] += ["Cover Type               Total    Unreachable   Inconclusive      Reachable"]
    patterns["warning"] += ["inconclusive", "inconclusives"]

    return patterns

def set_timeout(framework, step, timeout):
    """Set the timeout for a specific step"""
    timeout_value = f" -timeout {timeout} "
    if step == "rulecheck":
        framework.tool_flags["autocheck verify"] += timeout_value
    elif step == "xverify":
        framework.tool_flags["xcheck verify"] += timeout_value
    elif step == "reachability":
        framework.tool_flags["covercheck verify"] += timeout_value
    elif step == "prove":
        framework.tool_flags["formal verify"] += timeout_value

def generics_to_args(generics):
    """Converts a dict with generic:value pairs to the argument we have to
    pass to the tools"""
    string = ''
    for i in generics:
        string += f'-g {i}={generics[i]} '
    return string

def formal_initialize_rst(framework, rst, active_high=True, cycles=1):
    """
    Initialize reset for formal steps.
    """
    if active_high:
        line = f'formal init {{{rst}=1;##{cycles+1};{rst}=0}}'
        framework.init_reset.append(line)
    else:
        line = f'formal init {{{rst}=0;##{cycles+1};{rst}=1}}'
        framework.init_reset.append(line)

