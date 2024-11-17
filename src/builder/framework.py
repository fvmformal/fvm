# Python standard library imports
import sys
import os
import re
import glob
import shutil
import time
import subprocess
import pathlib
import fnmatch

# Third party imports
import argparse
from loguru import logger
from rich.console import Console
from rich.text import Text

# Our own imports
from src.builder import toolchains
from src.builder import logcounter
from src.builder import helpers
from src.builder.parse_design_rpt import *

# Error codes
BAD_VALUE    = "FVM exit condition: Bad value"
ERROR_IN_LOG = "FVM exit condition: Error in tool log"
CHECK_FAILED = "FVM exit condition: check_for_errors failed"

# Log formats
LOGFORMAT = '<cyan>FVM</cyan> | <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
LOGFORMAT_SUMMARY = '<cyan>FVM</cyan> | <green>Summary</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
#LOGFORMAT_TOOL = '<cyan>FVM</cyan> | <green>Tool</green> | <level>{level: <8}</level> | <level>{message}</level>'

def getlogformattool(design, step, tool):
    return f'<cyan>{design}.{step}</cyan> | <green>{tool=}</green> | ' + '<level>{level: <8}</level> | <level>{message}</level>'

# Steps, in order of execution, of the methodology
FVM_STEPS = [
    'lint',
    'friendliness',
    'reachability',
    'resets',
    'clocks',
    'prove'
    ]

# Create a rich console object
# TODO: force_terminal should enable color inside gitlab CI, but may break
# non-color terminals?
console = Console(force_terminal=True)

class fvmframework:

    def __init__(self):
        """Class constructor"""

        # Configure the argument parser
        parser = argparse.ArgumentParser(description='Run the formal tools')
        parser.add_argument('-v', '--verbose', default=False, action='store_true',
                help='Show full tool outputs. (default: %(default)s)')
        parser.add_argument('-l', '--list', default=False, action='store_true',
                help='Only list available methodology steps, but do not execute them. (default: %(default)s)')
        parser.add_argument('-o', '--outdir', default = "fvm_out",
                help='Output directory. (default: %(default)s)')
        parser.add_argument('-d', '--design',
                help='If set, run the specified design. If unset, run all designs. (default: %(default)s)')
        parser.add_argument('-s', '--step',
                help='If set, run the specified step. If unset, run all steps. (default: %(default)s)')
        parser.add_argument('-c', '--cont', default=False, action='store_true',
                help='Continue with next steps even if errors are detected. (default: %(default)s)')
        parser.add_argument('-g', '--gui', default=False, action='store_true',
                help='Show tool results with GUI after tool execution. (default: %(default)s)')
        parser.add_argument('-n', '--guinorun', default=False, action='store_true',
                help='Show already existing tool results with GUI, without running the tools again. (default: %(default)s)')

        # Get command-line arguments
        #
        # Since pytest also has command-line arguments, we may have a conflict
        # here, so get different arguments depending on whether the called
        # program is pytest or not
        #
        # If we are called by pytest, pass an empty list to argparse, because
        # the arguments received by pytest will not be recognized by our code
        # and thus all tests would fail. If we are not called by pytest, pass
        # the rest of sys.argv to argparse
        if re.search('pytest', sys.argv[0]):
            args = parser.parse_args([])
        else:
            args = parser.parse_args(sys.argv[1:])

        logger.trace(f'{args=}')
        self.verbose = args.verbose
        self.list = args.list
        self.outdir = args.outdir
        self.design = args.design
        self.step = args.step
        self.cont = args.cont
        self.gui = args.gui
        self.guinorun = args.guinorun

        # Make loglevel an instance variable
        if self.verbose :
            self.loglevel = "TRACE"
        else :
            self.loglevel = "INFO"

        # Create logger counter
        self.log_counter = logcounter.logcounter()

        # Clean logger format and handlers
        logger.remove()

        # Add log_counter as custom handler so log messages are counted
        # include all message types (from level 0 onwards) so they get recorded
        # even if they are not printed
        logger.add(self.log_counter, level=0)

        # Get log messages also in stderr. Only print format
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

        # Log the creation of the framework object
        logger.trace(f'Creating {self}')

        # Are we called from inside a script or from stdin?
        self.scriptname = helpers.getscriptname()
        logger.info(f'{self.scriptname=}')

        # Rest of instance variables
        # TODO : this is getting a bit big, we could consider restructuring
        # this, maybe defining a structure per toplevel
        self.toplevel = list()
        self.current_toplevel = ''
        self.vhdl_sources = list()
        self.psl_sources = list()
        self.skip_list = list()
        self.disabled_coverage = list()
        self.toolchain = "questa"
        self.vhdlstd = "2008"
        self.tool_flags = dict()
        self.resets = list()
        self.clocks = list()
        self.reset_domains = list()
        self.clock_domains = list()
        self.blackboxes = list()
        self.blackbox_instances = list()
        self.cutpoints = list()
        self.pre_hooks = dict()
        self.post_hooks = dict()

        # Specific tool defaults for each toolchain
        if self.toolchain == "questa":
            self.tool_flags["lint methodology"] = "ip -goal start"
            self.tool_flags["rdc generate report"] = "-resetcheck"
            self.tool_flags["cdc generate report"] = "-clockcheck"
            self.tool_flags["formal verify"] = "-auto_constraint_off -cov_mode"

        # Exit if args.step is unrecognized
        if args.step is not None:
            if args.step not in toolchains.TOOLS[self.toolchain]:
                logger.error(f'step {args.step} not available in {self.toolchain}. Available steps are: {list(toolchains.TOOLS[self.toolchain].keys())}')
                self.exit_if_required(BAD_VALUE)

    def add_vhdl_source(self, src):
        """Add a single VHDL source"""
        logger.info(f'Adding VHDL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'VHDL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.vhd', '.VHD', '.vhdl', '.VHDL'] :
            logger.warning(f'VHDL source {src=} does not have a typical VHDL extension, instead it has {extension=}')
        self.vhdl_sources.append(src)
        logger.debug(f'{self.vhdl_sources=}')

    def clear_vhdl_sources(self):
        """Removes all VHDL sources from the project"""
        logger.info(f'Removing all VHDL sources')
        self.vhdl_sources = []

    def add_psl_source(self, src):
        """Add a single PSL source"""
        logger.info(f'Adding PSL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'PSL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.psl', '.PSL'] :
            logger.warning(f'PSL source {src=} does not have a typical PSL extension extension, instead it has {extension=}')
        self.psl_sources.append(src)
        logger.debug(f'{self.psl_sources=}')

    def clear_psl_sources(self):
        """Removes all PSL sources from the project"""
        logger.info(f'Removing all PSL sources')
        self.psl_sources = []

    def add_vhdl_sources(self, globstr):
        """Add multiple VHDL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_vhdl_source(source)

    def add_psl_sources(self, globstr):
        """Add multiple PSL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in glob.glob(globstr):
            self.add_psl_source(source)

    def list_vhdl_sources(self):
        """List VHDL sources"""
        logger.info(f'{self.vhdl_sources=}')

    def list_psl_sources(self):
        """List PSL sources"""
        logger.info(f'{self.psl_sources=}')

    def list_sources(self):
        """List all sources"""
        self.list_vhdl_sources()
        self.list_psl_sources()

    def check_tool(self, tool):
        """Checks if toolname exists in PATH

        @param toolname: name of executable to look for in PATH"""
        path = shutil.which(tool)
        if path is None :
            logger.warning(f'{tool=} not found in PATH')
            ret = False
        else :
            logger.success(f'{tool=} found at {path=}')
            ret = True
        return ret

    def set_toplevel(self, toplevel):
        """Sets the name of the toplevel module. Multiple toplevels to analyze
        can be specified as a list. If a single toplevel is specified, this
        function converts it to a single-element list"""

        # TODO : check for duplicates inside the list!


        if isinstance(toplevel, str):
            self.toplevel = [toplevel]
        elif isinstance(toplevel, list):
            # Check for duplicates and throw an error if a toplevel is
            # specified more than once
            if len(toplevel) != len(set(toplevel)):
                logger.error(f'Duplicates exist in {toplevel=}')
                sys.exit(BAD_VALUE)
            else:
                self.toplevel = toplevel

        # If a design was specified, just run that design
        if self.design is not None:
            if self.design in self.toplevel:
                self.toplevel = [self.design]
            else:
                logger.error(f'Specified {args.design=} not in {self.toplevel=}, did you add it with set_toplevel()?')

        # Initialize a dict structure for the results
        self.results = {}
        for design in self.toplevel:
            self.results[design] = {}
            for step in FVM_STEPS:
                self.results[design][step] = {}

    # TODO : we could make this function accept also a list, but not sure if it
    # is worth it since the user could just call it inside a loop
    def skip(self, step, design='*'):
        """Allow to skip specific steps and/or designs. Accepts the wilcards
        '*' and '*'"""
        self.skip_list.append(f'{design}.{step}')

    def disable_coverage(self, covtype, design='*'):
        """Allow disabling specific coverage collection types. Allowed values
        for covtype are 'observability', 'reachability',
        'bounded_reachability', and 'signoff'"""
        allowed_covtypes = ['observability', 'signoff', 'reachability', 'bounded_reachability']
        assert covtype in allowed_covtypes, f'Specified {covtype=} not in {allowed_covtypes=}'
        self.disabled_coverage.append(f'{design}.prove.{covtype}')

    # TODO: not sure if we need to let the user pass arguments, I don't think
    # it will be necessary for now
    def run_hook(hook):
        """Run a user-specified hook"""
        if callable(hook):
            return hook()
        else:
            logger.error(f'{hook=} is not callable, only functions or other callable objects can be passed as hooks')

    def set_pre_hook(self, hook, step, design='*'):
        self.pre_hooks[design] = dict()
        self.pre_hooks[design][step] = hook

    def set_post_hook(self, hook, step, design='*'):
        self.post_hooks[design] = dict()
        self.post_hooks[design][step] = hook

    def set_loglevel(self, loglevel):
        """Sets the logging level for the build and test framework.

        @param loglevel: must be one of loguru's allowed log levels: TRACE,
        DEBUG, INFO, SUCCESS, WARNING, ERROR, or CRITICAL"""
        # TODO : maybe we will just remove some of these loglevels as valid
        # options if we end up using those log levels to indicate normal
        # operation of our framework
        logger.remove()
        self.loglevel = loglevel
        logger.add(self.log_counter, level=0)
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

    def set_logformat(self, logformat):
        logger.remove()
        logger.add(self.log_counter, level=0)
        logger.add(sys.stderr, level=self.loglevel, format=logformat)

    def get_log_counts(self) :
        return self.log_counter.get_counts()

    def log(self, severity, string) :
        """Make the logger visible from the outside, so we can log messages
        from within our test files, by calling fvm.log()"""
        # Convert the severity to lowercase and use that as a function name (so
        # we call logger.info, logger.warning, etc.)
        # getattr gets the method by name from the specified class (in this
        # case, logger)
        logfunction = getattr(logger, severity.lower())
        logfunction(string)

    def check_errors(self) :
        """Returns True if there is at least one recorded ERROR or CRITICAL
        message, False otherwise"""
        ret = False
        msg_counts = self.get_log_counts()
        #print(f'{msg_counts=}')

        # Use a different format for summary messages
        logger.remove()
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT_SUMMARY)

        logger.info(f'Got {msg_counts["TRACE"]=} trace messages')
        logger.info(f'Got {msg_counts["DEBUG"]=} debug messages')
        logger.info(f'Got {msg_counts["INFO"]=} info messages')
        if msg_counts['SUCCESS'] > 0 :
            logger.success(f'Got {msg_counts["SUCCESS"]=} success messages')
        else :
            logger.info(f'Got {msg_counts["SUCCESS"]=} success messages')
        if msg_counts['WARNING'] > 0 :
            logger.warning(f'Got {msg_counts["WARNING"]=} warning messages')
        else :
            logger.success(f'Got {msg_counts["WARNING"]=} warning messages')
        if msg_counts['ERROR'] > 0 :
            logger.error(f'Got {msg_counts["ERROR"]=} error messages')
            ret = True
        else :
            logger.success(f'Got {msg_counts["ERROR"]=} error messages')
        if msg_counts['CRITICAL'] > 0 :
            logger.critical(f'Got {msg_counts["CRITICAL"]=} critical messages')
            ret = True
        else :
            logger.success(f'Got {msg_counts["CRITICAL"]=} critical messages')


        # Restore the original log format and loglevel
        logger.remove()
        logger.add(self.log_counter, level=0)
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

        if ret :
          self.exit_if_required(CHECK_FAILED)

        return ret

    # From now on, these are the functions that are toolchain-dependent
    # (meaning that they have tool-specific code)

    def set_toolchain(self, toolchain) :
        if toolchain not in toolchains.TOOLS :
            logger.error(f'{toolchain=} not supported')
            self.exit_if_required(BAD_VALUE)
        else :
            self.toolchain = toolchain

    def check_library_exists(self, path) :
        if self.toolchain == "questa" :
            expectedfile = path + "_info"
        logger.debug(f'checking if {expectedfile=} exists')
        if os.path.exists(path) :
            ret = True
        else :
            ret = False
        return ret

    def cmd_create_library(self, lib):
        if self.toolchain == "questa":
            cmd = toolchains.TOOLS[self.toolchain]["createemptylib"] + ' ' + lib
        return cmd

    def create_f_file(self, filename, sources):
        with open(filename, "w") as f:
            for src in sources:
                print(src, file=f)

    # TODO : check that port_list must be an actual list()
    def add_clock_domain(self, name, port_list, asynchronous=None,
                         synchronous=None, ignore=None, posedge=None,
                         negedge=None, module=None, inout_clock_in=None,
                         inout_clock_out=None):
        domain = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding clock domain: {domain}')
        self.clock_domains.append(domain)

    # TODO : check that port_list must be an actual list()
    def add_reset_domain(self, name, port_list, asynchronous=None,
                         synchronous=None, active_high=None, active_low=None,
                         is_set=None, no_reset=None, module=None, ignore=None):
        domain = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding reset domain: {domain}')
        self.reset_domains.append(domain)

    def add_reset(self, name, module=None, group=None, active_low=None,
                  active_high=None, asynchronous=None, synchronous=None,
                  external=None, ignore=None, remove=None):
        """Adds a reset to the design. 'name' can be a signal/port name or a
        pattern, such as rst*."""
        # Copy all arguments to a dict, excepting self
        reset = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding reset: {reset}')
        self.resets.append(reset)

    def add_clock(self, name, module=None, group=None, period=None,
                  waveform=None, external=None, ignore=False, remove=False):
        """Adds a clock to the design. 'name' can be a signal/port name or a
        pattern, such as clk*."""
        clock = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding clock: {clock}')
        self.clocks.append(clock)

    def blackbox(self, entity):
        """Blackboxes all instances of an entity/module"""
        logger.trace(f'blackboxing entity: {entity}')
        self.blackboxes.append(entity)

    def blackbox_instance(self, instance):
        """Blackboxes a specific instance of an entity/module"""
        logger.trace(f'blackboxing instance: {instance}')
        self.blackbox_instances.append(instance)

    def cutpoint(self, signal, module=None, resetval=None, condition=None,
                 driver=None, wildcards_dont_match_hierarchy_separators=False):
        """Sets a specifig signal as a cutpoint"""
        cutpoint = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding cutpoint: {cutpoint}')
        self.cutpoints.append(cutpoint)

    def setup(self, design):
        """Create the output directory and the scripts for a design, but do not
        run anything"""
        # Create the output directories, but do not throw an error if it already
        # exists
        os.makedirs(self.outdir, exist_ok=True)
        self.current_toplevel = design
        path = self.outdir+'/'+self.current_toplevel
        os.makedirs(path, exist_ok=True)

        if self.toolchain == "questa":
            # Create .f files and .do files
            self.create_f_file(f'{path}/design.f', self.vhdl_sources)
            self.create_f_file(f'{path}/properties.f', self.psl_sources)
            self.genlintscript("lint.do", path)
            self.genfriendlinessscript("friendliness.do", path)
            self.genreachabilityscript("reachability.do", path)
            self.genresetscript("resets.do", path)
            self.genclockscript("clocks.do", path)
            self.genprovescript("prove.do", path)

    def gencompilescript(self, filename, path):
        """Generate script to compile design sources"""
        # TODO : we must also compile the Verilog sources, if they exist
        # TODO : we must check for the case of only-verilog designs (no VHDL files)
        # TODO : we must check for the case of only-VHDL designs (no verilog files)
        # TODO : support libraries other than work (see #154)
        """ This is used as header for the other scripts, since we need to have
        a compiled netlist in order to do anything"""
        with open(path+'/'+filename, "w") as f:
            print('onerror exit', file=f)
            print('if {[file exists work]} {',file=f)
            print('    vdel -all', file=f)
            print('}', file=f)
            print(f'vlib {self.get_tool_flags("vlib")} work', file=f)
            print(f'vmap {self.get_tool_flags("vmap")} work work', file=f)
            print(f'vcom {self.get_tool_flags("vcom")} -{self.vhdlstd} -autoorder -f {path}/design.f', file=f)
            print('', file=f)

    def gen_reset_config(self, filename, path):
        with open(path+'/'+filename, "a") as f:
            # TODO : let the user specify clock names, polarities, sync/async,
            # clock domains and reset domains
            # Clock trees can be both active high and low when some logic is
            # reset when the reset is high and other logic is reset when it is
            # low.
            # Also, reset signals can drive trees of both synchronous and
            # asynchronous resets
            for reset in self.resets:
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

    def gen_reset_domain_config(self, filename, path):
        with open(path+'/'+filename, "a") as f:
            for domain in self.reset_domains:
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

    def gen_clock_config(self, filename, path):
        with open(path+'/'+filename, "a") as f:
            for clock in self.clocks:
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

    def gen_clock_domain_config(self, filename, path):
        with open(path+'/'+filename, "a") as f:
            for domain in self.clock_domains:
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

    # TODO : set sensible defaults here and allow for user optionality too
    # i.e., lint methodology, goal, etc
    def genlintscript(self, filename, path):
        """Generate script to run Lint"""
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'lint methodology {self.get_tool_flags("lint methodology")}', file=f)
            print(f'lint run -d {self.current_toplevel} {self.get_tool_flags("lint run")}', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too
    def genfriendlinessscript(self, filename, path):
        """Generate script to run AutoCheck, which also generates a report we
        analyze to determine the design's formal-friendliness"""
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'autocheck compile {self.get_tool_flags("autocheck compile")} -d {self.current_toplevel}', file=f)
            print(f'autocheck verify {self.get_tool_flags("autocheck verify")}', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too,
    # such as allowing the user to specify the covercheck directives
    # TODO : if a .ucdb file is specified as argument, run the post-simulation
    # analysis instead of the pre-simulation analysis (see
    # https://git.woden.us.es/eda/fvm/-/issues/37#note_4252)
    def genreachabilityscript(self, filename, path):
        """Generate a script to run CoverCheck"""
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'covercheck compile {self.get_tool_flags("covercheck compile")} -d {self.current_toplevel}', file=f)
            # if .ucdb file is specified:
            #    print('covercheck load ucdb {ucdb_file}', file=f)
            #    print(f'covercheck verify -covered_items', file=f)
            print(f'covercheck {self.get_tool_flags("covercheck verify")} verify', file=f)
            print('exit', file=f)

    def genresetscript(self, filename, path):
        # We first write the header to compile the netlist  and then append
        # (mode "a") the tool-specific instructions
        self.gencompilescript(filename, path)
        self.gen_clock_config(filename, path)
        self.gen_clock_domain_config(filename, path)
        self.gen_reset_config(filename, path)
        self.gen_reset_domain_config(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'rdc run -d {self.current_toplevel} {self.get_tool_flags("rdc run")}', file=f)
            print(f'rdc generate report reset_report.rpt {self.get_tool_flags("rdc generate report")};', file=f)
            print('rdc generate tree -reset reset_tree.rpt;', file=f)
            print('exit', file=f)

    def genclockscript(self, filename, path):
        """Generate script to run Clock Domain Crossing"""
        # We first write the header to compile the netlist  and then append
        # (mode "a") the tool-specific instructions
        self.gencompilescript(filename, path)
        self.gen_clock_config(filename, path)
        self.gen_clock_domain_config(filename, path)
        self.gen_reset_config(filename, path)
        self.gen_reset_domain_config(filename, path)
        with open(path+'/'+filename, "a") as f:
            # TODO : let the user specify clock names, clock domains and reset domains
            # TODO : also look at reconvergence, and other warnings detected
            #print('netlist clock clk -period 50', file=f)

            # Enable reconvergence to remove warning [hdl-271]
            # TODO : add option to disable reconvergence?
            print(f'cdc reconvergence on', file=f)
            print(f'cdc run -d {self.current_toplevel} {self.get_tool_flags("cdc run")}', file=f)
            print(f'cdc generate report clock_report.rpt {self.get_tool_flags("cdc generate report")}', file=f)
            print('cdc generate tree -clock clock_tree.rpt;', file=f)
            print('exit', file=f)

    # TODO : we will need arguments for the clocks, timeout, we probably need
    # to detect compile order if vcom doesn't detect it, set the other options
    # such as timeout... and also throw some errors if any option is not
    # specified. This is not trivial. Also, in the future we may want to
    # specify verilog files with vlog, etc...
    # TODO : can we also compile the PSL files using a .f file?
    def genprovescript(self, filename, path):
        """Generate script to run PropCheck"""
        self.gencompilescript(filename, path)
        # Only add the clocks since we don't want to add any extra constraint
        # Also, adding the clock domain make propcheck throw errors because
        # output ports in the clock domain cannot be constrained
        self.gen_clock_config(filename, path)
        with open(path+'/'+filename, "a") as f:
            print('', file=f)
            print('## Run PropCheck', file=f)
            #print('log_info "***** Running formal compile (compiling formal model)..."', file=f)

            print('formal compile ', end='', file=f)
            print(f'-d {self.current_toplevel} ', end='', file=f)
            for i in self.psl_sources :
                print(f'-pslfile {i} ', end='', file=f)
            print('-include_code_cov ', end='', file=f)
            print(f'{self.get_tool_flags("formal compile")}', file=f)

            for blackbox in self.blackboxes:
                print(f'netlist blackbox {blackbox}', file=f)

            for blackbox_instance in self.blackbox_instances:
                print(f'netlist blackbox_instance {blackbox_instance}', file=f)

            for cutpoint in self.cutpoints:
                string = f'netlist cutpoint {cutpoint["signal"]}'
                if cutpoint["module"] is not None:
                    string += f' -module {cutpoint["module"]}'
                if cutpoint["resetval"] is True:
                    string += ' -reset_value'
                if cutpoint["condition"] is not None:
                    string += f'-cond {cutpoint["condition"]}'
                if cutpoint["drive"] is not None:
                    string += f'-cond {cutpoint["driver"]}'
                if cutpoint["wildcards_dont_match_hierarchy"] is True:
                    string += '-match_local_scope'
                print(string, file=f)

            #print('log_info "***** Running formal verify (model checking)..."', file=f)
            print(f'formal verify {self.get_tool_flags("formal verify")}', file=f)
            print('', file=f)
            print('## Compute Formal Coverage', file=f)
            #print('log_info "***** Running formal verify to get coverage..."', file=f)
            # TODO : maybe we should run coverage collection in separate
            # scripts so we can better capture if there have been any errors,
            # and also to annotate if they have been skipped
            #print('log_info "***** Running formal generate coverage..."', file=f)
            if not self.is_disabled('observability'):
                print('formal generate coverage -cov_mode o', file=f)
            if not self.is_disabled('signoff'):
                print('formal verify -auto_constraint_off -cov_mode signoff -timeout 10m', file=f)
                print('formal generate coverage -cov_mode s', file=f)
            if not self.is_disabled('reachability'):
                print('formal verify -auto_constraint_off -cov_mode reachability -timeout 10m', file=f)
                print('formal generate coverage -cov_mode r', file=f)
            # TODO : bounded reachability requires at least an inconclusive
            # assertion.
            # TODO : it is clear then we need to run coverage in another
            # script, so we may add or not the bounded reachability coverage
            # collection
            #if not self.is_disabled('bounded_reachability'):
            #    print('formal verify -auto_constraint_off -cov_mode bounded_reachability -timeout 10m', file=f)
            #    print('formal generate coverage -cov_mode b', file=f)
            print(f'formal generate testbenches {self.get_tool_flags("formal generate testbenches")}', file=f)
            print('formal generate report', file=f)
            print('', file=f)
            print('exit', file=f)

    def run(self, skip_setup=False):
        """Run everything"""
        logger.info(f'Designs: {self.toplevel}')
        for design in self.toplevel:
            logger.info(f'Running {design=}')
            self.run_design(design, skip_setup)

        self.pretty_summary()
        self.generate_reports()
        err = self.check_errors()
        if err :
          self.exit_if_required(CHECK_FAILED)

    def run_design(self, design, skip_setup=False):
        """Run all available/selected methodology steps for a design"""
        # Create all necessary scripts
        if not skip_setup:
            self.setup(design)

        # Run all available/selected steps/tools
        # Call the run_step() function for each available step
        # If a 'step' argument is specified, just run that specific step
        # TODO : the run code is duplicated below, we could think of some way
        # of deduplicating it
        if self.step is None:
            for step in FVM_STEPS:
                if self.is_skipped(design, step):
                    logger.info(f'{step=} of {design=} skipped by skip() function, will not run')
                    self.results[design][step]['status'] = 'skip'
                elif step in toolchains.TOOLS[self.toolchain]:
                    self.run_pre_hook(design, step)
                    err = self.run_step(design, step)
                    if err:
                        self.exit_if_required(ERROR_IN_LOG)
                    self.run_post_step(design, step)
                    self.run_post_hook(design, step)
                else:
                    logger.info(f'{step=} not available in {self.toolchain=}, skipping')
                    self.results[design][step]['status'] = 'skip'
        else:
            self.run_pre_hook(design, self.step)
            err = self.run_step(design, self.step)
            if err:
                self.exit_if_required(ERROR_IN_LOG)
            self.run_post_step(design, self.step)
            self.run_post_hook(design, self.step)

    def is_skipped(self, design, step):
        """Returns True if design.step must not be run, otherwise returns False"""
        for skip_str in self.skip_list:
            if fnmatch.fnmatch(f'{design}.{step}', skip_str):
                return True
        return False

    def is_disabled(self, covtype):
        """Returns True if design.prove.covtype must not be collected, otherwise returns False"""
        for disable_str in self.disabled_coverage:
            if fnmatch.fnmatch(f'{self.current_toplevel}.prove.{covtype}', disable_str):
                return True
        return False

    # TODO : we have some duplicated code in the way we run commands, becase
    # the code sort of repeats for the GUI invocations. We must see how we can
    # deduplicate this so this function does not get unwieldy
    def run_step(self, design, step):
        """Run a specific step of the methodology"""
        err = False
        path = self.outdir+'/'+self.current_toplevel
        open_gui = False
        # If called with a specific step, run that specific step
        if step in toolchains.TOOLS[self.toolchain] :
            tool = toolchains.TOOLS[self.toolchain][step][0]
            wrapper = toolchains.TOOLS[self.toolchain][step][1]
            logger.info(f'{step=}, running {tool=} with {wrapper=}')
            logger.debug(f'Running {tool=} with {wrapper=}')
            if self.toolchain == "questa":
                cmd = [wrapper, '-c', '-od', path, '-do', f'{path}/{step}.do']
                if self.list == True :
                    logger.info(f'Available step: {step}. Tool: {tool}, command = {" ".join(cmd)}')
                elif self.guinorun == True :
                    logger.info(f'{self.guinorun=}, will not run {step=} with {tool=}')
                else :
                    logger.trace(f'command: {" ".join(cmd)=}')
                    cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, step, tool, self.verbose)
                    stdout_err = self.logcheck(cmd_stdout, design, step, tool)
                    stderr_err = self.logcheck(cmd_stderr, design, step, tool)
                    logfile = f'{path}/{step}.log'
                    logger.info(f'{step=}, {tool=}, finished, output written to {logfile}')
                    with open(logfile, 'w') as f :
                        f.write(cmd_stdout)
                        f.write(cmd_stderr)
                    # We cannot exit here immediately because then we wouldn't
                    # be able to open the GUI if there is any error, but we can
                    # record the error and propagate it outside the function
                    if stdout_err or stderr_err:
                        err = True
                    if stdout_err or stderr_err:
                        self.results[design][step]['status'] = 'fail'
                    else:
                        self.results[design][step]['status'] = 'pass'
                    if self.gui :
                        open_gui = True
                if self.guinorun and self.list == False :
                    open_gui = True
                # TODO : maybe check for errors also in the GUI?
                # TODO : maybe run the GUI processes without blocking
                # the rest of the steps? For that we would probably
                # need to pass another option to run_cmd
                # TODO : code here can be deduplicated by having the database
                # names (.db) in a dictionary -> just open {tool}.db
                if open_gui:
                    logger.info(f'{step=}, {tool=}, opening results with GUI')
                    cmd = [wrapper, f'{path}/{tool}.db']
                    logger.trace(f'command: {" ".join(cmd)=}')
                    self.run_cmd(cmd, design, step, tool, self.verbose)

        else :
            logger.error(f'No tool available for {step=} in {self.toolchain=}')
            self.exit_if_required(BAD_VALUE)

        # TODO : return output values
        # pass / fail / skipped / disabled, and also warnings, errors,
        # successes, and for prove the number of asserts, proven, fired,
        # inconclusives, cover, covered, uncoverable... etc

        return err


    def run_cmd(self, cmd, design, step, tool, verbose = True):
        """Run a specific command"""
        self.set_logformat(getlogformattool(design, step, tool))
        logger.info(f'command: {" ".join(cmd)}')

        start_time = time.perf_counter()
        process = subprocess.Popen (
                  cmd,
                  stdout  = subprocess.PIPE,
                  stderr  = subprocess.PIPE,
                  text    = True,
                  bufsize = 1
                  )

        # Initialize variables where to store command stdout/stderr
        stdout_lines = list()
        stderr_lines = list()

        if not verbose:
            print('Running: ', end='', flush=True)

        # If verbose, read and print stdout and stderr in real-time
        with process.stdout as stdout, process.stderr as stderr:
            for line in iter(stdout.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn, success = self.linecheck(line)
                    if err:
                        logger.error(line.rstrip())
                    elif warn:
                        logger.warning(line.rstrip())
                    elif success:
                        logger.success(line.rstrip())
                    else:
                        logger.trace(line.rstrip())
                # If not verbose, print dots
                else:
                    print('.', end='', flush=True)
                stdout_lines.append(line)  # Save to list

            for line in iter(stderr.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn, success = self.linecheck(line)
                    if err:
                        logger.error(line.rstrip())
                    elif warn:
                        logger.warning(line.rstrip())
                    elif success:
                        logger.success(line.rstrip())
                    else:
                        logger.trace(line.rstrip())
                # If not verbose, print dots
                else:
                    print('.', end='', flush=True)
                stderr_lines.append(line)  # Save to list

        # Wait for the process to complete and get the return code
        retval = process.wait()

        # After the process has finished, calculate elapsed time
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.results[design][step]['elapsed_time'] = elapsed_time

        # If not verbose, print the final carriage return for the dots
        if not verbose:
            print(' Finished', flush=True)

        # Join captured output
        captured_stdout = ''.join(stdout_lines)
        captured_stderr = ''.join(stderr_lines)

        # Raise an exception if the return code is non-zero
        if retval != 0:
            raise subprocess.CalledProcessError(retval, cmd, output=captured_stdout, stderr=captured_stderr)

        self.set_logformat(LOGFORMAT)

        return captured_stdout, captured_stderr

    def run_pre_hook(self, design, step):
        """Run the pre_hook if it exists. Only one hook is run: specific design
        hooks take priority before globally specified hooks"""
        self.run_hook_if_defined(self.pre_hooks, design, step)

    def run_post_hook(self, design, step):
        """Run the post_hook if it exists. Only one hook is run: specific
        design hooks take priority before globally specified hooks"""
        self.run_hook_if_defined(self.post_hooks, design, step)

    def run_hook_if_defined(self, hooks, design, step):
        """Run a hook if it exists. Only one hook is run: specific design
        hooks take priority before globally specified hooks"""
        if design in hooks:
            if step in hooks[design]:
                run_hook(self.hooks[design][step])
        elif '*' in hooks:
            if step in hooks['*']:
                run_hook(hooks['*'][step])

    def run_post_step(self, design, step):
        """Run post processing for a specific step of the methodology"""
        # Currently we only do post-processing after the friendliness step
        logger.trace('run_post_step, {design=}, {step=})')
        path = self.outdir+'/'+self.current_toplevel
        if step == 'friendliness':
            rpt = path+'/autocheck_design.rpt'
            data = data_from_design_summary(rpt)
            self.results[design][step]['data'] = data
            self.results[design][step]['score'] = friendliness_score(data)

    def logcheck(self, result, design, step, tool):
        """Check log for errors"""
        err_in_log = False
        self.set_logformat(getlogformattool(design, step, tool))
        for line in result.splitlines() :
            err, warn, success = self.linecheck(line)
            # If we are in verbose mode, still check if there are errors /
            # warnings / etc. but do not duplicate the messages
            if err :
                if not self.verbose:
                    logger.error(f'ERROR detected in {step=}, {tool=}, {line=}')
                err_in_log = True
            elif warn :
                if not self.verbose:
                    logger.warning(f'WARNING detected in {step=}, {tool=}, {line=}')
            elif success :
                if not self.verbose:
                    logger.success(f'SUCCESS detected in {step=}, {tool=}, {line=}')
        self.set_logformat(LOGFORMAT)
        return err_in_log

    # TODO: this must be independized from the toolchain and possibly from the
    # methodology step/tool. We should have a list of pass/clear (strings that
    # look like errors/warnings but are not, such as error summaries), error
    # and warning strings, and look for those in that order
    def linecheck(self, line):
        """Check for errors and warnings in log lines. Use casefold() for
        robust case-insensitive comparison"""
        err = False
        warn = False
        success = False
        if 'Errors: 0' in line:
            pass  # Avoid signalling an error on tool error summaries without errors
        elif 'Error (0)' in line:
            pass  # Avoid signalling an error on tool error summaries without errors
        elif 'Command : onerror' in line:
            pass  # Avoid signalling an error when the tool log echoes our "onerror exit"
        elif 'error'.casefold() in line.casefold():
            err = True
        elif 'fatal'.casefold() in line.casefold():
            err = True
        elif 'Warning (0)'.casefold() in line.casefold():
            pass # Avoid signalling a warning on tool warning summaries without warnings
        elif 'warning'.casefold() in line.casefold():
            warn = True
        elif 'Cover Type' in line:
            pass # Avoid signalling a warning on the header of the summary table
        elif 'Fired' in line:
            err = True
        elif 'Proven' in line:
            success = True
        elif 'Vacuous' in line:
            warn = True
        elif 'Inconclusive' in line:
            warn = True
        elif 'Uncoverable' in line:
            err = True
        elif 'Covered' in line:
            success = True
        return err, warn, success

    def set_tool_flags(self, tool, flags):
        """Set user-defined flags for a specific tool"""
        self.tool_flags[tool] = flags

    def get_tool_flags(self, tool):
        """Get user-defined flags for a specific tool. If flags are not set,
        returns an empty string, so the script generators can just call this
        function and expect it to always return a value of string type"""
        if tool in self.tool_flags:
            flags = self.tool_flags[tool]
        else:
            flags = ""
        return flags

    def pretty_summary(self):
        """Prints the final summary"""
        # TODO : use rich or a similar python package to format a table
        # TODO : print the status for each design.step
        # TODO : color the status
        # TODO : print also number of warnings and errors, and all relevant
        # information from PropCheck (number of
        # assume/assert/fired/proven/cover/covered/uncoverable/etc. For this,
        # we may need to post-process the prove step log
        # TODO : print elapsed time

        # Calculate maximum length of {design}.{step} so we can pad later
        maxlen = 0
        for design in self.toplevel:
            for step in FVM_STEPS:
                curlen = len(f'{design}.{step}')
                if curlen > maxlen:
                    maxlen = curlen

        # Accumulators for total values
        total_time = 0
        total_pass = 0
        total_fail = 0
        total_skip = 0
        total_cont = 0
        total_stat = 0

        text_header = Text("==== Summary ==============================================")
        console.print(text_header)

        for design in self.toplevel:
            for step in FVM_STEPS:
                total_cont += 1
                # Only print pass/fail/skip, the rest of steps where not
                # selected by the user so there is no need to be redundant
                if 'status' in self.results[design][step]:
                    total_stat += 1
                    status = self.results[design][step]['status']
                    if status == 'pass':
                        style = 'bold green'
                        total_pass += 1
                    elif status == 'fail':
                        style = 'bold red'
                        total_fail += 1
                    elif status == 'skip':
                        style = 'bold yellow'
                        total_skip += 1
                    text = Text()
                    text.append(status, style=style)
                    text.append(' ')
                    design_step = f'{design}.{step}'
                    text.append(f'{design_step:<{maxlen}}')
                    if step == 'friendliness':
                        score = self.results[design][step]["score"]
                        score_str = f' (score: {score:.2f}%)'
                    else:
                        score_str =  '                '
                    text.append(score_str)
                    if "elapsed_time" in self.results[design][step]:
                        time = self.results[design][step]["elapsed_time"]
                        total_time += time
                        time_str = f' ({helpers.readable_time(time)})'
                        text.append(time_str)
                    #text.append(f' result={self.results[design][step]}', style='white')
                    console.print(text)
                    #print(f'{status} {design}.{step}, result={self.results[design][step]}')
        text_footer = Text("===========================================================")
        console.print(text_footer)
        text = Text()
        text.append('pass', style='bold green')
        text.append(f' {total_pass} of {total_cont}')
        console.print(text)
        if total_fail != 0:
            text = Text()
            text.append('fail', style='bold red')
            text.append(f' {total_fail} of {total_cont}')
            console.print(text)
        if total_skip != 0:
            text = Text()
            text.append('skip', style='bold yellow')
            text.append(f' {total_skip} of {total_cont}')
            console.print(text)
        if total_stat != total_cont:
            text = Text()
            text.append('omit', style='bold white')
            text.append(f' {total_cont - total_stat} of {total_cont} (not executed due to early exit)')
            console.print(text)
        console.print(text_footer)
        text = Text()
        text.append(f'Total time  : {helpers.readable_time(total_time)}\n')
        text.append(f'Elapsed time: (not yet implemented)')
        console.print(text)
        console.print(text_footer)

    # TODO: actually write this
    def generate_reports(self):
        """Generates output reports"""
        from junit_xml import TestSuite, TestCase
        pass


    def exit_if_required(self, errorcode):
        """Exits with a specific error code if the continue flag (cont) is not
        set"""
        if self.cont:
            pass
        else:
            self.pretty_summary()
            self.generate_reports()
            sys.exit(errorcode)
