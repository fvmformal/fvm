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
from datetime import datetime
from io import StringIO
from collections import OrderedDict
from shlex import join

# Third party imports
import argparse
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Our own imports
from fvm import logcounter
from fvm import helpers
from fvm import generate_test_cases
from fvm import reports
from fvm.steps import steps
from fvm.toolchains import toolchains
from fvm.drom2psl.generator import generator

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

# TODO : these two constants (FVM_STEPS and FVM_POST_STEPS) will be removed
# when the steps are programmatically initialized
#
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

# Create a rich console object
# TODO: force_terminal should enable color inside gitlab CI, but may break
# non-color terminals? maybe we should use environment variables instead? see https://rich.readthedocs.io/en/stable/console.html#environment-variables
# For CI systems that support colors but where we don't want any interactivity
# (such as gitlab-ci), we set force_terminal to True and force_interactive to
# False
console = Console(force_terminal=True, force_interactive=False)

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

        self.logger = logger
        self.logger.trace(f'{args=}')
        self.verbose = args.verbose
        self.list = args.list
        self.outdir = args.outdir
        self.resultsdir = f'{self.outdir}/fvm_results'  # For the .xml results
        self.reportdir = f'{self.outdir}/fvm_report'  # For the Allure dashboard
        self.design = args.design
        self.step = args.step
        self.cont = args.cont
        self.gui = args.gui
        self.guinorun = args.guinorun
        self.flexlm_logdir = os.path.join(self.outdir, ".flexlm.log")
        self.env = os.environ.copy()
        self.env["FLEXLM_DIAGNOSTICS_PATH"] = self.flexlm_logdir

        # Make loglevel an instance variable
        if self.verbose :
            self.loglevel = "TRACE"
        else :
            self.loglevel = "INFO"

        # Create logger counter
        self.log_counter = logcounter.logcounter()

        # Clean logger format and handlers
        self.logger.remove()

        # Add log_counter as custom handler so log messages are counted
        # include all message types (from level 0 onwards) so they get recorded
        # even if they are not printed
        self.logger.add(self.log_counter, level=0)

        # Get log messages also in stderr. Only print format
        self.logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

        # Log the creation of the framework object
        self.logger.trace(f'Creating {self}')

        # Are we being called from inside a script or from stdin?
        self.is_interactive = helpers.is_interactive()
        if self.is_interactive:
            self.logger.info('Running interactively')
        else:
            self.logger.info('Running from within a script')

        self.scriptname = helpers.getscriptname()
        self.logger.info(f'{self.scriptname=}')

        # Let's define a prefix for our test results, in case the user wants to
        # run different formal.py files and create a report that includes all
        # of them.
        #
        # By default, we define the prefix as the directory where formal.py is
        #   e.g.: if script: /home/user/mydesign/formal.py , prefix = mydesign
        # If running in interactive mode, 'scriptname' points to the directory
        # from where we run the python interpreter, so let's get that directory
        # and append '_interactive' to it
        #   e.g.: if dir: /home/user/mydesign , prefix = mydesign_interactive
        #
        # Users can also set a prefix using fvmframwork.set_prefix(prefix)
        if self.is_interactive:
            self.prefix = os.path.basename(self.scriptname)+'_interactive'
            self.logger.info(f'Running interactively, {self.prefix=}')
        else:
            self.prefix = os.path.basename(os.path.dirname(self.scriptname))
            self.logger.info(f'Running inside a script, {self.prefix=}')

        # Rest of instance variables
        # TODO : this is getting a bit big, we could consider restructuring
        # this, maybe defining a structure per toplevel
        self.toplevel = list()
        self.current_toplevel = ''
        self.start_time_setup = None
        self.init_reset = list()
        self.vhdl_sources = list()
        self.libraries_from_vhdl_sources = list()
        self.psl_sources = list()
        self.drom_sources = list()
        self.drom_generated_psl = list()
        self.skip_list = list()
        self.allow_failure_list = list()
        self.disabled_coverage = list()
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
        self.designs = list()
        self.design_configs = dict()

        # Get the toolchain (questa, sby, etc), assign sensible default options
        # defined in the selected toolchain, and define the methdology steps
        # according to what the toolchain does actually support
        self.toolchain = toolchains.get_toolchain()
        self.logger.info(f'{self.toolchain=}')
        if self.toolchain not in toolchains.toolchains :
            self.logger.error(f'{self.toolchain=} not supported')
            self.exit_if_required(BAD_VALUE)
        self.tool_flags = toolchains.get_default_flags(self.toolchain)
        self.logger.info(f'{self.tool_flags=}')
        self.steps = steps()
        toolchains.define_steps(self.steps, self.toolchain)
        self.logger.info(f'{steps=}')

        # Exit if args.step is unrecognized
        if args.step is not None:
            if args.step not in self.steps.steps:
                self.logger.error(f'step {args.step} not available in {self.toolchain}. Available steps are: {list(self.steps.steps.keys())}')
                self.exit_if_required(BAD_VALUE)

    def set_toolchain(self, toolchain) :
        """Allows to override the FVM_TOOLCHAIN environment variable and set a
        different toolchain"""
        if toolchain not in toolchains.toolchains :
            self.logger.error(f'{toolchain=} not supported')
            self.exit_if_required(BAD_VALUE)
        else :
            self.toolchain = toolchain

    def run_command(self, command):
        """Execute a system command and handle errors."""
        try:
            result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f'Command succeeded: {command}')
            self.logger.debug(f'STDOUT: {result.stdout.strip()}')
            if result.stderr.strip():
                self.logger.debug(f'STDERR: {result.stderr.strip()}')
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Command failed: {command}')
            self.logger.error(f'Error: {e.stderr.strip()}')
            raise

    def add_vhdl_source(self, src, library="work"):
        """Add a single VHDL source"""
        self.logger.info(f'Adding VHDL source: {src}')
        if not os.path.exists(src) :
            self.logger.error(f'VHDL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.vhd', '.VHD', '.vhdl', '.VHDL'] :
            self.logger.warning(f'VHDL source {src=} does not have a typical VHDL extension, instead it has {extension=}')
        self.vhdl_sources.append(src)
        self.libraries_from_vhdl_sources.append(library)
        self.logger.debug(f'{self.vhdl_sources=}')

    def clear_vhdl_sources(self):
        """Removes all VHDL sources from the project"""
        self.logger.info(f'Removing all VHDL sources')
        self.vhdl_sources = []

    def add_psl_source(self, src):
        """Add a single PSL source"""
        self.logger.info(f'Adding PSL source: {src}')
        if not os.path.exists(src) :
            self.logger.error(f'PSL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.psl', '.PSL'] :
            self.logger.warning(f'PSL source {src=} does not have a typical PSL extension extension, instead it has {extension=}')
        self.psl_sources.append(src)
        self.logger.debug(f'{self.psl_sources=}')

    def clear_psl_sources(self):
        """Removes all PSL sources from the project"""
        self.logger.info(f'Removing all PSL sources')
        self.psl_sources = []

    def add_drom_source(self, src, library="work"):
        """Add a single wavedrom source"""
        self.logger.info(f'Adding wavedrom source: {src}')
        if not os.path.exists(src) :
            self.logger.error(f'wavedrom source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.json', '.JSON', '.drom', '.wavedrom'] :
            self.logger.warning(f'wavedrom source {src=} does not have a typical wavedrom extension, instead it has {extension=}')
        self.drom_sources.append(src)
        self.logger.debug(f'{self.drom_sources=}')

    def clear_drom_sources(self):
        """Removes all wavedrom sources from the project"""
        self.logger.info(f'Removing all wavedrom sources')
        self.drom_sources = []

    def add_vhdl_sources(self, globstr, library="work"):
        """Add multiple VHDL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_vhdl_source(source, library)

    def add_psl_sources(self, globstr):
        """Add multiple PSL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in glob.glob(globstr):
            self.add_psl_source(source)

    def add_drom_sources(self, globstr, library="work"):
        """Add multiple wavedrom sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_drom_source(source, library)

    def list_vhdl_sources(self):
        """List VHDL sources"""
        self.logger.info(f'{self.vhdl_sources=}')

    def list_psl_sources(self):
        """List PSL sources"""
        self.logger.info(f'{self.psl_sources=}')

    def list_drom_sources(self):
        """List wavedrom sources"""
        self.logger.info(f'{self.drom_sources=}')

    def list_sources(self):
        """List all sources"""
        self.list_vhdl_sources()
        self.list_psl_sources()
        self.list_drom_sources()

    def check_tool(self, tool):
        """Checks if toolname exists in PATH

        @param toolname: name of executable to look for in PATH"""
        path = shutil.which(tool)
        if path is None :
            self.logger.warning(f'{tool=} not found in PATH')
            ret = False
        else :
            self.logger.success(f'{tool=} found at {path=}')
            ret = True
        return ret

    def set_prefix(self, prefix):
        if type(prefix) != str:
            error(f'Specified {prefix=} is not a string, {type(prefix)=}')
        self.prefix = prefix

    def set_toplevel(self, toplevel):
        """Sets the name of the toplevel module. Multiple toplevels to analyze
        can be specified as a list. If a single toplevel is specified, this
        function converts it to a single-element list"""

        if isinstance(toplevel, str):
            self.toplevel = [toplevel]
        elif isinstance(toplevel, list):
            # Check for duplicates and throw an error if a toplevel is
            # specified more than once
            if len(toplevel) != len(set(toplevel)):
                self.logger.error(f'Duplicates exist in {toplevel=}')
                sys.exit(BAD_VALUE)
            else:
                self.toplevel = toplevel

        # TODO : in the future, the design output dirs may have the library
        # name, such as libname.design or libname/design, so that error message
        # will not be necessary because there won't be any clashes with fvm_*
        # directories
        if 'fvm_dashboard' in toplevel or 'fvm_reports' in toplevel:
            self.logger.error("toplevels can not have the following reserved names: fvm_dashboard, fvm_reports")
            sys.exit(BAD_VALUE)

        # If a design was specified, just run that design
        if self.design is not None:
            if self.design in self.toplevel:
                self.toplevel = [self.design]
            else:
                self.logger.error(f'Specified {args.design=} not in {self.toplevel=}, did you add it with set_toplevel()?')

    def init_results(self):
        # TODO: this must be initialized per design configuration, but to do
        # that we must do it somewhere else
        # Initialize a dict structure for the results
        self.results = {}
        for design in self.toplevel:
            if design in self.design_configs:
                for config in self.design_configs[design]:
                    self.designs.append(f'{design}.{config["name"]}')
            else:
                self.designs.append(f'{design}')

        for design in self.designs:
            self.results[design] = {}
            for step in FVM_STEPS + FVM_POST_STEPS:
                self.results[design][step] = {}
                self.results[design][step]['message'] = ''
                self.results[design][step]['stdout'] = ''
                self.results[design][step]['stderr'] = ''
                self.results[design][step]['summary'] = {}

    def add_config(self, design, name, generics):
        """Adds a design configuration. The design configuration has a name and
        values for its generics, and applies to a specific design. If at least
        one design configuration exists, the default configuration is not
        used"""

        # Check that the configuration is for a valid design
        if design not in self.toplevel:
            self.logger.error(f'Specified {design=} not in {self.toplevel=}')

        # Initialize the design configurations list if it doesn't exist
        if design not in self.design_configs:
            self.design_configs[design] = list()

        # Create the configuration as a dict() and append it to the design
        # configurations list
        config = dict()
        config["name"] = name
        config["generics"] = generics
        self.design_configs[design].append(config)
        self.logger.trace(f'Added configuration {self.design_configs} to {design=}')

    # TODO : we could make this function accept also a list, but not sure if it
    # is worth it since the user could just call it inside a loop
    def skip(self, step, design='*'):
        """Allow to skip specific steps and/or designs. Accepts the wilcards
        '*' and '*'"""
        self.skip_list.append(f'{design}.{step}')

    # TODO : use message
    # TODO : what does "use message mean"?
    def allow_failure(self, step, design='*', message='Failure allowed'):
        """Allow failures for specific steps and/or designs. Accepts the wildcards
        '*' and '*'"""
        self.allow_failure_list.append(f'{design}.{step}')

    def disable_coverage(self, covtype, design='*'):
        """Allow disabling specific coverage collection types. Allowed values
        for covtype are 'observability', 'reachability',
        'bounded_reachability', and 'signoff'"""
        allowed_covtypes = ['observability', 'signoff', 'reachability', 'bounded_reachability']
        assert covtype in allowed_covtypes, f'Specified {covtype=} not in {allowed_covtypes=}'
        self.disabled_coverage.append(f'{design}.prove.{covtype}')

    def set_timeout(self, step, timeout):
        """Set the timeout for a specific step"""
        toolchains.set_timeout(self, self.toolchain, step, timeout)

    def generics_to_args(self, generics):
        """Converts a dict with generic:value pairs to the argument we have to
        pass to the tools"""
        return toolchains.generics_to_args(self.toolchain, generics)

    def formal_initialize_rst(self, rst, active_high=True, cycles=1):
        """
        Initialize reset for formal steps.
        """
        if active_high:
            line = f'formal init {{{rst}=1;##{cycles+1};{rst}=0}}'
            self.init_reset.append(line)
        else:
            line = f'formal init {{{rst}=0;##{cycles+1};{rst}=1}}'
            self.init_reset.append(line)

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
        self.logger.remove()
        self.loglevel = loglevel
        self.logger.add(self.log_counter, level=0)
        self.logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

    def set_logformat(self, logformat):
        self.logger.remove()
        self.logger.add(self.log_counter, level=0)
        self.logger.add(sys.stderr, level=self.loglevel, format=logformat)

    def get_log_counts(self) :
        return self.log_counter.get_counts()

    def log(self, severity, string) :
        """Make the logger visible from the outside, so we can log messages
        from within our test files, by calling fvm.log()"""
        # Convert the severity to lowercase and use that as a function name (so
        # we call logger.info, logger.warning, etc.)
        # getattr gets the method by name from the specified class (in this
        # case, logger)
        logfunction = getattr(self.logger, severity.lower())
        logfunction(string)

    def check_errors(self) :
        """Returns True if there is at least one recorded ERROR or CRITICAL
        message, False otherwise"""
        ret = False
        msg_counts = self.get_log_counts()
        #print(f'{msg_counts=}')

        # Use a different format for summary messages
        self.logger.remove()
        self.logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT_SUMMARY)

        self.logger.info(f'Got {msg_counts["TRACE"]=} trace messages')
        self.logger.info(f'Got {msg_counts["DEBUG"]=} debug messages')
        self.logger.info(f'Got {msg_counts["INFO"]=} info messages')
        if msg_counts['SUCCESS'] > 0 :
            self.logger.success(f'Got {msg_counts["SUCCESS"]=} success messages')
        else :
            self.logger.info(f'Got {msg_counts["SUCCESS"]=} success messages')
        if msg_counts['WARNING'] > 0 :
            self.logger.warning(f'Got {msg_counts["WARNING"]=} warning messages')
        else :
            self.logger.success(f'Got {msg_counts["WARNING"]=} warning messages')
        if msg_counts['ERROR'] > 0 :
            self.logger.error(f'Got {msg_counts["ERROR"]=} error messages')
            ret = True
        else :
            self.logger.success(f'Got {msg_counts["ERROR"]=} error messages')
        if msg_counts['CRITICAL'] > 0 :
            self.logger.critical(f'Got {msg_counts["CRITICAL"]=} critical messages')
            ret = True
        else :
            self.logger.success(f'Got {msg_counts["CRITICAL"]=} critical messages')


        # Restore the original log format and loglevel
        self.logger.remove()
        self.logger.add(self.log_counter, level=0)
        self.logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

        if ret :
          self.exit_if_required(CHECK_FAILED)

        return ret

    # TODO : check that port_list must be an actual list()
    def add_clock_domain(self, name, port_list, asynchronous=None,
                         synchronous=None, ignore=None, posedge=None,
                         negedge=None, module=None, inout_clock_in=None,
                         inout_clock_out=None):
        domain = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding clock domain: {domain}')
        self.clock_domains.append(domain)

    # TODO : check that port_list must be an actual list()
    def add_reset_domain(self, name, port_list, asynchronous=None,
                         synchronous=None, active_high=None, active_low=None,
                         is_set=None, no_reset=None, module=None, ignore=None):
        domain = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding reset domain: {domain}')
        self.reset_domains.append(domain)

    def add_reset(self, name, module=None, group=None, active_low=None,
                  active_high=None, asynchronous=None, synchronous=None,
                  external=None, ignore=None, remove=None):
        """Adds a reset to the design. 'name' can be a signal/port name or a
        pattern, such as rst*."""
        # Copy all arguments to a dict, excepting self
        reset = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding reset: {reset}')
        self.resets.append(reset)

    def add_clock(self, name, module=None, group=None, period=None,
                  waveform=None, external=None, ignore=False, remove=False):
        """Adds a clock to the design. 'name' can be a signal/port name or a
        pattern, such as clk*."""
        clock = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding clock: {clock}')
        self.clocks.append(clock)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, entity)
    def blackbox(self, entity):
        """Blackboxes all instances of an entity/module"""
        self.logger.trace(f'blackboxing entity: {entity}')
        self.blackboxes.append(entity)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, instance)
    def blackbox_instance(self, instance):
        """Blackboxes a specific instance of an entity/module"""
        self.logger.trace(f'blackboxing instance: {instance}')
        self.blackbox_instances.append(instance)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, ...and the rest)
    def cutpoint(self, signal, module=None, resetval=None, condition=None,
                 driver=None, wildcards_dont_match_hierarchy_separators=False):
        """Sets a specifig signal as a cutpoint"""
        cutpoint = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding cutpoint: {cutpoint}')
        self.cutpoints.append(cutpoint)

    def run(self, skip_setup=False):
        """Run everything"""
        self.init_results()

        self.start_time_setup = datetime.now().isoformat()
        # TODO: correctly manage self.list here (self.list is True if -l or
        # --list was provided as a command-line argument)

        self.logger.info(f'Designs: {self.toplevel}')
        for design in self.toplevel:
            self.logger.info(f'Running {design=}')
            if self.list:
                self.list_design(design)
            else:
                self.run_design(design, skip_setup)

        reports.pretty_summary(self, self.logger)
        reports.generate_reports(self, self.logger)
        reports.generate_allure(self, self.logger)
        err = self.check_errors()
        if err :
          self.exit_if_required(CHECK_FAILED)

    def setup(self):
        for design in self.toplevel:
            if design in self.design_configs:
                self.logger.trace(f'{design=} has configs: {self.design_configs}')
                for config in self.design_configs[design]:
                    self.setup_design(design, config)
            else:
                self.logger.trace(f'{design=} has no configs, setting up default config')
                self.setup_design(design, None)

    def list_design(self, design, skip_setup=False):
        """List all available/selected methodology steps for a design"""
        # If configurations exist, list them all
        self.logger.info(f'Listing {design=} with configs: {self.design_configs}')
        if design in self.design_configs:
            self.logger.trace(f'{design=} has configs: {self.design_configs}')
            for config in self.design_configs[design]:
                self.list_configuration(design, config)
        else:
            self.logger.trace(f'{design=} has no configs, running default config')
            self.list_configuration(design, None)

    def run_design(self, design, skip_setup=False):
        """Run all available/selected methodology steps for a design"""
        # If configurations exist, run them all
        self.logger.info(f'Running {design=} with configs: {self.design_configs}')
        if design in self.design_configs:
            self.logger.trace(f'{design=} has configs: {self.design_configs}')
            for config in self.design_configs[design]:
                self.run_configuration(design, config, skip_setup)
        else:
            self.logger.trace(f'{design=} has no configs, running default config')
            self.run_configuration(design, None, skip_setup)

    def list_configuration(self, design, config=None):
        """List all available/selected methodology steps for a design
        configuration"""

        if config is not None:
            design = f'{design}.{config["name"]}'
        else:
            design = design

        # List all available/selected steps/tools
        # Call the list_step() function for each available step
        # If a 'step' argument is specified, just list that specific step
        # TODO : the list code is duplicated below, we could think of some way
        # of deduplicating it
        if self.step is None:
            for step in FVM_STEPS:
                if self.is_skipped(design, step):
                    self.logger.trace(f'{step=} of {design=} skipped by skip() function, will not list')
                    self.results[design][step]['status'] = 'skip'
                elif step in self.steps.steps:
                    self.list_step(design, step)
                else:
                    self.logger.trace(f'{step=} not available in {self.toolchain=}, skipping')
                    self.results[design][step]['status'] = 'skip'
        else:
            self.list_step(design, self.step)

    def list_step(self, design, step):
        self.logger.trace(f'{design}.{step}')
        self.results[design][step]['status'] = 'skip'

    def run_configuration(self, design, config=None, skip_setup=False):
        """Run all available/selected methodology steps for a design
        configuration"""

        # Archive previous executions of the design
        # If the design directory already exists, move it to a subdirectory
        # called "previous_executions" and append a timestamp to the directory
        # name, so we don't lose the previous results.
        # If GUINORUN is set, we are just showing previous results, so
        # don't archive anything
        if not self.guinorun:
            if config is not None:
                previous_design = f"{design}.{config['name']}"
            else:
                previous_design = design
            current_dir = os.path.join(self.outdir, previous_design)
            archive_dir = os.path.join(self.outdir, "previous_executions")
            if os.path.exists(current_dir):
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                timestamp = datetime.now().isoformat()
                target_dir = os.path.join(archive_dir, f'{previous_design}_{timestamp}')
                shutil.move(current_dir, target_dir)

        # Create all necessary scripts
        if not skip_setup:
            self.setup_design(design, config)

        if config is not None:
            design = f'{design}.{config["name"]}'
        else:
            design = design

        self.current_toplevel = design

        # Run all available/selected steps/tools
        # Call the run_step() function for each available step
        # If a 'step' argument is specified, just run that specific step
        # TODO : the run code is duplicated below, we could think of some way
        # of deduplicating it
        if self.step is None:
            self.logger.info(self.steps.steps)
            # TODO : this is a quick hack so we don't lose the questa
            # functionality, since the license has expired and we can't test
            # with the questa tools. The desired final behavior is to just
            # iterate on self.steps.steps, as seen in the line below
            #for step in self.steps.steps:
            if self.toolchain == 'questa':
                steps_to_perform = FVM_STEPS
            elif self.toolchain == 'sby':
                steps_to_perform = self.steps.steps

            for step in steps_to_perform:  # should be self.steps.steps
                if self.is_skipped(design, step):
                    self.logger.info(f'{step=} of {design=} skipped by skip() function, will not run')
                    self.results[design][step]['status'] = 'skip'
                elif step in self.steps.steps:
                    # TODO : allow pre_hooks to return errors and stop the run
                    # if they fail
                    self.run_pre_hook(design, step)
                    err = self.run_step(design, step)
                    if err:
                        self.exit_if_required(ERROR_IN_LOG)
                    # TODO : allow post_steps to return errors and stop the run
                    # if they fail
                    self.run_post_step(design, step)
                    # TODO : allow post_hooks to return errors and stop the run
                    # if they fail
                    self.run_post_hook(design, step)
                else:
                    self.logger.info(f'{step=} not available in {self.toolchain=}, skipping')
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

    def is_failure_allowed(self, design, step):
        """Returns True if design.step is allowed to fail, otherwise returns False"""
        for failure_str in self.allow_failure_list:
            if fnmatch.fnmatch(f'{design}.{step}', failure_str):
                return True
        return False

    def is_disabled(self, covtype):
        """Returns True if design.prove.covtype must not be collected, otherwise returns False"""
        for disable_str in self.disabled_coverage:
            if fnmatch.fnmatch(f'{self.current_toplevel}.prove.{covtype}', disable_str):
                return True
        return False

    def set_tool_flags(self, tool, flags):
        """Set user-defined flags for a specific tool"""
        # TODO : warn the user if neither -jix nor -justify_initial_x is in
        # self.tool_flags["formal verify"]: it could lead to failing
        # assumptions during simulation
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

    def clear_directory(self, directory_path):
        try:
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)

                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
        except Exception as e:
            print(f"Error occurred while clearing the directory: {e}")

    def exit_if_required(self, errorcode):
        """Exits with a specific error code if the continue flag (cont) is not
        set"""
        if self.cont:
            pass
        else:
            reports.pretty_summary(self, self.logger)
            reports.generate_reports(self, self.logger)
            reports.generate_allure(self, self.logger)
            sys.exit(errorcode)

    # TODO : design argument may be redundant since we have
    # self.current_toplevel
    # TODO : we could also put step in self.current_step so we don't have to
    # also pass that argument
    def run_cmd(self, cmd, design, step, tool, verbose = True, cwd=None):
        """Run a specific command"""
        self.set_logformat(getlogformattool(design, step, tool))
        if cwd is not None:
            cwd_for_debug = cwd
        else:
            cwd_for_debug = self.outdir
        self.logger.info(f'command: {join(cmd)}, working directory: {cwd_for_debug}')

        timestamp = datetime.now().isoformat()
        self.results[design][step]['timestamp'] = timestamp

        start_time = time.perf_counter()
        process = subprocess.Popen (
                  cmd,
                  cwd        = cwd,
                  stdout     = subprocess.PIPE,
                  stderr     = subprocess.PIPE,
                  text       = True,
                  bufsize    = 1,
                  env        = self.env,
                  preexec_fn = os.setsid
                )

        import signal
        ctrl_c_pressed = [False]

        def handle_sigint(signum, frame):
            self.logger.error("Ctrl+C detected")
            ctrl_c_pressed[0] = True
            os.killpg(os.getpgid(process.pid), signal.SIGINT)

        signal.signal(signal.SIGINT, handle_sigint)

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
                        self.logger.error(line.rstrip())
                    elif warn:
                        self.logger.warning(line.rstrip())
                    elif success:
                        self.logger.success(line.rstrip())
                    else:
                        self.logger.trace(line.rstrip())
                # If not verbose, print dots
                else:
                    print('.', end='', flush=True)
                stdout_lines.append(line)  # Save to list

            for line in iter(stderr.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn, success = self.linecheck(line)
                    if err:
                        self.logger.error(line.rstrip())
                    elif warn:
                        self.logger.warning(line.rstrip())
                    elif success:
                        self.logger.success(line.rstrip())
                    else:
                        self.logger.trace(line.rstrip())
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

        self.results[design][step]['stdout'] += captured_stdout
        self.results[design][step]['stderr'] += captured_stderr

        # Raise an exception if the return code is non-zero
        if retval != 0 and ctrl_c_pressed[0] is False:
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
                self.run_hook(hooks[design][step], step, design)
        elif '*' in hooks:
            if step in hooks['*']:
                self.run_hook(hooks['*'][step], step, design)

    # TODO: not sure if we need to let the user pass arguments, I don't think
    # it will be necessary for now
    def run_hook(self, hook, step, design):
        """Run a user-specified hook"""
        if callable(hook):
            return hook(step, design)
        else:
            self.logger.error(f'{hook=} is not callable, only functions or other callable objects can be passed as hooks')

    def generate_psl_from_drom_sources(self, path):
        self.logger.info(f'{self.drom_sources=}')
        if self.drom_sources:
            drom2psl_outdir = os.path.join(self.outdir, path)
            os.makedirs(drom2psl_outdir, exist_ok=True)
            generator(self.drom_sources, outdir=drom2psl_outdir)
            self.drom_generated_psl = [pathlib.Path(src).with_suffix('.psl') for src in self.drom_sources]

    def setup_design(self, design, config = None):
        """Create the output directory and the scripts for a design, but do not
        run anything"""
        # Create the output directories, but do not throw an error if they
        # already exist
        os.makedirs(self.outdir, exist_ok=True)
        os.makedirs(self.flexlm_logdir, exist_ok=True)
        self.current_toplevel = design
        self.generate_psl_from_drom_sources(os.path.join(self.current_toplevel, 'drom2psl'))

        if config is not None:
            extra_path = f'.{config["name"]}'
            self.generic_args = self.generics_to_args(config["generics"])
        else:
            extra_path = ''
            self.generic_args = ''

        path = f'{self.outdir}/{self.current_toplevel}'+extra_path
        self.current_path = path

        os.makedirs(path, exist_ok=True)

        # Run the assigned setup function for each step
        for step in self.steps.steps :
            #self.logger.trace(f'Setting up {design=}, {step=}')
            self.steps.steps[step]["setup"](self, path)

    def logcheck(self, result, design, step, tool):
        """Check log for errors"""

        # Set the specific log format for this design, step and tool
        self.set_logformat(getlogformattool(design, step, tool))

        # Temporarily add a handler to capture logs
        log_stream = StringIO()
        handler_id = self.logger.add(log_stream, format="{time} {level} {message}")

        err_in_log = False
        for line in result.splitlines() :
            err, warn, success = self.linecheck(line)

            if self.is_failure_allowed(design, step) == True and err:
                warn = True
                err = False
            # If we are in verbose mode, still check if there are errors /
            # warnings / etc. but do not duplicate the messages
            if err :
                if not self.verbose:
                    self.logger.error(f'ERROR detected in {step=}, {tool=}, {line=}')
                err_in_log = True
            elif warn :
                if not self.verbose:
                    self.logger.warning(f'WARNING detected in {step=}, {tool=}, {line=}')
            elif success :
                if not self.verbose:
                    self.logger.success(f'SUCCESS detected in {step=}, {tool=}, {line=}')

        # Capture the messages into the results
        self.results[design][step]['message'] += log_stream.getvalue()

        # Remove the handler to stop capturing messages
        self.logger.remove(handler_id)
        log_stream.close()

        # Restore the previous log format
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
        elif 'Note: (vsim-12126) Error and warning message counts have been restored' in line:
            pass  # Avoid signalling an error on this note from vsim
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

    def run_step(self, design, step):
        """Run a specific step of the methodology"""
        console.rule(f'[bold white]{design}.{step}[/bold white]')
        err = False
        path = self.current_path
        open_gui = False

        if step in self.steps.steps:
            run_stdout, run_stderr, err = self.steps.steps[step]["run"](self, path)
            logfile = f'{path}/{step}/{step}.log'
            self.logger.info(f'{step=}, finished, output written to {logfile}')
            with open(logfile, 'w') as f :
                f.write(run_stdout)
                f.write(run_stderr)

        else :
            self.logger.error(f'No tool available for {step=} in {self.toolchain=}')
            self.exit_if_required(BAD_VALUE)

        # TODO : return output values
        # pass / fail / skipped / disabled, and also warnings, errors,
        # successes, and for prove the number of asserts, proven, fired,
        # inconclusives, cover, covered, uncoverable... etc

        return err

    # TODO: we also need a setup_post_step
    def setup_post_step(self, design, step):
        pass

    def run_post_step(self, design, step):
        """Run post processing for a specific step of the methodology"""
        # Currently we only do post-processing after the friendliness and prove
        # steps
        self.logger.trace(f'run_post_step, {design=}, {step=})')
        path = self.current_path
        # TODO : quick hack to prototype sby support since we cannot change the
        # questa-dependent code (well we can, but we have no way of checking if
        # we broke it since our license is expired)
        # TODO : run_post_step should probably run a _single_ step, and maybe
        # we can have a run_post_steps function that calls run_post_step
        # multiple times?
        err = False
        if step in self.steps.post_steps:
            for post_step in self.steps.post_steps[step]:
                if not self.is_skipped(design, f'{step}.{post_step}'):
                    console.rule(f'[bold white]{design}.{step}.{post_step}[/bold white]')
                    err = self.steps.post_steps[step][post_step]["run"](self, path)
                    logfile = f'{path}/{step}.log'
                    self.logger.info(f'{step}.{post_step}, finished, output written to {logfile}')
                    #with open(logfile, 'w') as f :
                    #    f.write(run_stdout)
                    #    f.write(run_stderr)
                else:
                    self.results[design][f'{step}.{post_step}']['status'] = 'skip'
        # TODO : correctly process errors

        return err

    # ******************************************************************* #
    # ******************************************************************* #
    # From now on, these are (or should be!) the functions that are
    # toolchain-dependent (meaning that they have tool-specific code)
    # TODO : this functionality must be moved to the specific toolchain
    # code, and encapsulated here (the same as we do in set_timeout)
    # ******************************************************************* #
    # ******************************************************************* #

    # TODO: are we really using these functions? I don't see them being called
    # neither in concepts/ nor in examples/

    # This is questa-specific
    def add_external_library(self, name, src):
        """Add an external library"""
        self.logger.info(f'Adding the external library: {name} from {src}')
        if not os.path.exists(src) :
            self.logger.error(f'External library not found: {name} from {src}')
            self.exit_if_required(BAD_VALUE)
        try:
            self.logger.info(f'Compiling library {name} from {src}')
            self.run_command(f'vlib {name}')
            self.run_command(f'vmap {name} {name}')
            vhdl_files = [os.path.join(root, file)
                        for root, _, files in os.walk(src)
                        for file in files if file.endswith(('.vhd', '.VHD', '.vhdl', '.VHDL'))]
            if vhdl_files:
                self.logger.info(f'Compiling VHDL files for external library {name}')
                self.run_command(f'vcom -work {name} -{self.vhdlstd} -autoorder {" ".join(vhdl_files)}')
        except Exception as e:
            self.logger.error(f'Error compiling library {name}: {e}')
            self.exit_if_required(BAD_VALUE)
        self.logger.info(f'Successfully added and mapped library {name}')

    # This is questa-specific
    def add_precompiled_library(self, name, path):
        """Add a precompiled external library"""
        self.logger.info(f'Adding precompiled library: {name} from {path}')
        if not os.path.exists(path):
            self.logger.error(f'Precompiled library path not found: {path}')
            self.exit_if_required(BAD_VALUE)
        try:
            self.logger.info(f'Mapping precompiled library {name} to {path}')
            self.run_command(f'vmap {name} {path}')
        except Exception as e:
            self.logger.error(f'Error mapping precompiled library {name}: {e}')
            self.exit_if_required(BAD_VALUE)
        self.logger.info(f'Successfully mapped precompiled library {name}')

