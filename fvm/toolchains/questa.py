import os
from collections import OrderedDict

# TODO : For all this file: probably forward slashes (/) are not portable and
# we should use a library to manage path operations, such as os.path or pathlib
# (pathlib seems to be more recommended)

# For the Questa tools, each tool is run through a wrapper which is the actual
# command that must be run in the command-line
tools = {
        # step           : ["tool",       "wrapper"],
        "lint"           : ["lint",       "qverify"],
        "friendliness"   : ["autocheck",  "qverify"],
        "rulecheck"      : ["autocheck",  "qverify"],
        "xverify"        : ["xcheck",     "qverify"],
        "reachability"   : ["covercheck", "qverify"],
        "fault"          : ["slec",       "qverify"],
        "resets"         : ["rdc",        "qverify"],
        "clocks"         : ["cdc",        "qverify"],
        "prove"          : ["propcheck",  "qverify"],
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

def create_f_file(filename, sources):
    with open(filename, "w") as f:
        for src in sources:
            print(src, file=f)

def gencompilescript(framework, filename, path):
    """Generate script to compile design sources"""
    # TODO : we must also compile the Verilog sources, if they exist
    # TODO : we must check for the case of only-verilog designs (no VHDL files)
    # TODO : we must check for the case of only-VHDL designs (no verilog files)
    # TODO : libraries folder should be inside fvm_out as per #268
    library_path = f"libraries"
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

def setup_lint(framework, path):
    """Generate script to run Lint"""
    print("**** setup lint ****")
    filename = "lint.do"
    gencompilescript(framework, filename, path)
    with open(f'{path}/{filename}', "a") as f:
        print(f'lint methodology {framework.get_tool_flags("lint methodology")}', file=f)
        print(f'lint run -d {framework.current_toplevel} {framework.get_tool_flags("lint run")} {framework.generic_args}', file=f)
        print('exit', file=f)

def run_lint():
    print("**** run lint ****")
    pass

def setup_friendliness(framework, path):
    print("**** setup friendliness ****")
    """Generate script to compile AutoCheck, which also generates a report we
    analyze to determine the design's formal-friendliness"""
    filename = "friendliness.do"
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        print(f'autocheck compile {framework.get_tool_flags("autocheck compile")} -d {framework.current_toplevel} {framework.generic_args}', file=f)
        print('exit', file=f)

def run_friendliness():
    print("**** run friendliness ****")
    pass

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
        print(f'autocheck verify {framework.get_tool_flags("autocheck verify")}', file=f)
        print('exit', file=f)

def run_rulecheck():
    print("**** run rulecheck ****")
    pass

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

def run_xverify():
    print("**** run xverify ****")
    pass

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

def run_reachability():
    print("**** run reachability ****")
    pass

def setup_fault(framework, path):
    print("**** setup fault ****")
    filename = "fault.do"
    """Generate a script to run SLEC"""
    gencompilescript(framework, filename, path)
    with open(path+'/'+filename, "a") as f:
        for line in framework.init_reset:
            print(line, file=f)
        parts = framework.current_toplevel.rsplit(".", 1)
        if len(parts) == 2:
            lib, design = parts
            print(f'slec configure -spec -d {design} -work {lib}', file=f)
            print(f'slec configure -impl -d {design} -work {lib}', file=f)
        else:
            design = parts[0]
            print(f'slec configure -spec -d {design}', file=f)
            print(f'slec configure -impl -d {design}', file=f)

        for cutpoint in framework.cutpoints:
            string = f'netlist cutpoint impl.{cutpoint["signal"]}'
            if cutpoint["module"] is not None:
                string += f' -module {cutpoint["module"]}'
            if cutpoint["resetval"] is True:
                string += ' -reset_value'
            if cutpoint["condition"] is not None:
                string += f'-cond {cutpoint["condition"]}'
            if cutpoint["driver"] is not None:
                string += f'-cond {cutpoint["driver"]}'
            if cutpoint["wildcards_dont_match_hierarchy_separators"] is True:
                string += '-match_local_scope'
            print(string, file=f)
        print(f'slec compile {framework.generic_args}', file=f)
        print(f'slec verify -auto_constraint_off -justify_initial_x', file=f)
        print(f'slec generate report', file=f)
        print(f'slec generate waveforms -vcd', file=f)
        print('exit', file=f)

def run_fault():
    print("**** run fault ****")
    pass

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

def run_resets():
    print("**** run resets ****")
    pass

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

def run_clocks():
    print("**** run clocks ****")
    pass

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

def run_prove():
    print("**** run prove ****")
    pass

def setup_prove_simcover(framework, path):
    print("**** setup prove_simcover ****")
    pass

def run_prove_simcover():
    print("**** run prove_simcover ****")
    pass

def setup_prove_formalcover(framework, path):
    print("**** setup prove_formalcover ****")
    pass

def run_prove_formalcover():
    print("**** run prove_formalcover ****")
    pass

def define_steps(steps):
    steps.add_step('lint', setup_lint, run_lint)
    steps.add_step('friendliness', setup_friendliness, run_friendliness)
    steps.add_step('rulecheck', setup_rulecheck, run_rulecheck)
    steps.add_step('xverify', setup_xverify, run_xverify)
    steps.add_step('reachability', setup_reachability, run_reachability)
    steps.add_step('fault', setup_fault, run_fault)
    steps.add_step('resets', setup_resets, run_resets)
    steps.add_step('clocks', setup_clocks, run_clocks)
    steps.add_step('prove', setup_prove, run_prove)
    steps.add_post_step('prove', 'simcover', setup_prove_simcover, run_prove_simcover)
    steps.add_post_step('prove', 'formalcover', setup_prove_formalcover, run_prove_formalcover)

