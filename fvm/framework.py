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

# Third party imports
import argparse
from loguru import logger
from rich.console import Console
from rich.text import Text

# Our own imports
from fvm import logcounter
from fvm import helpers
from fvm import generate_test_cases
from fvm import reports
from fvm.steps import steps
from fvm.toolchains import toolchains
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
# TODO : why is this parser import different?
from fvm.parsers.parse_design_rpt import *

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

        logger.trace(f'{args=}')
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

        # Are we being called from inside a script or from stdin?
        self.is_interactive = helpers.is_interactive()
        if self.is_interactive:
            logger.info('Running interactively')
        else:
            logger.info('Running from within a script')

        self.scriptname = helpers.getscriptname()
        logger.info(f'{self.scriptname=}')

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
            logger.info(f'Running interactively, {self.prefix=}')
        else:
            self.prefix = os.path.basename(os.path.dirname(self.scriptname))
            logger.info(f'Running inside a script, {self.prefix=}')

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
        self.reachability_summary = dict()
        self.property_summary = dict()
        self.formalcover_summary = dict()
        self.simcover_summary = dict()
        self.lint_summary = dict()
        self.rulecheck_summary = dict()
        self.xverify_summary = dict()
        self.resets_summary = dict()
        self.clocks_summary = dict()
        self.fault_summary = dict()

        # Get the toolchain (questa, sby, etc), assign sensible default options
        # defined in the selected toolchain, and define the methdology steps
        # according to what the toolchain does actually support
        self.toolchain = toolchains.get_toolchain()
        self.tool_flags = toolchains.get_default_flags(self.toolchain)
        self.steps = steps()
        toolchains.define_steps(self.steps, self.toolchain)
        logger.info(f'{steps=}')

        # Exit if args.step is unrecognized
        if args.step is not None:
            if args.step not in toolchains.TOOLS[self.toolchain]:
                logger.error(f'step {args.step} not available in {self.toolchain}. Available steps are: {list(toolchains.TOOLS[self.toolchain].keys())}')
                self.exit_if_required(BAD_VALUE)

    def set_toolchain(self, toolchain) :
        """Allows to override the FVM_TOOLCHAIN environment variable and set a
        different toolchain"""
        if toolchain not in toolchains.TOOLS :
            logger.error(f'{toolchain=} not supported')
            self.exit_if_required(BAD_VALUE)
        else :
            self.toolchain = toolchain

    def run_command(self, command):
        """Execute a system command and handle errors."""
        try:
            result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f'Command succeeded: {command}')
            logger.debug(f'STDOUT: {result.stdout.strip()}')
            if result.stderr.strip():
                logger.debug(f'STDERR: {result.stderr.strip()}')
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f'Command failed: {command}')
            logger.error(f'Error: {e.stderr.strip()}')
            raise

    def add_vhdl_source(self, src, library="work"):
        """Add a single VHDL source"""
        logger.info(f'Adding VHDL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'VHDL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.vhd', '.VHD', '.vhdl', '.VHDL'] :
            logger.warning(f'VHDL source {src=} does not have a typical VHDL extension, instead it has {extension=}')
        self.vhdl_sources.append(src)
        self.libraries_from_vhdl_sources.append(library)
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

    def add_vhdl_sources(self, globstr, library="work"):
        """Add multiple VHDL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_vhdl_source(source, library)

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
                logger.error(f'Duplicates exist in {toplevel=}')
                sys.exit(BAD_VALUE)
            else:
                self.toplevel = toplevel

        # TODO : in the future, the design output dirs may have the library
        # name, such as libname.design or libname/design, so that error message
        # will not be necessary because there won't be any clashes with fvm_*
        # directories
        if 'fvm_dashboard' in toplevel or 'fvm_reports' in toplevel:
            logger.error("toplevels can not have the following reserved names: fvm_dashboard, fvm_reports")
            sys.exit(BAD_VALUE)

        # If a design was specified, just run that design
        if self.design is not None:
            if self.design in self.toplevel:
                self.toplevel = [self.design]
            else:
                logger.error(f'Specified {args.design=} not in {self.toplevel=}, did you add it with set_toplevel()?')

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

    def add_config(self, design, name, generics):
        """Adds a design configuration. The design configuration has a name and
        values for its generics, and applies to a specific design. If at least
        one design configuration exists, the default configuration is not
        used"""

        # Check that the configuration is for a valid design
        if design not in self.toplevel:
            logger.error(f'Specified {design=} not in {self.toplevel=}')

        # Initialize the design configurations list if it doesn't exist
        if design not in self.design_configs:
            self.design_configs[design] = list()

        # Create the configuration as a dict() and append it to the design
        # configurations list
        config = dict()
        config["name"] = name
        config["generics"] = generics
        self.design_configs[design].append(config)
        logger.trace(f'Added configuration {self.design_configs} to {design=}')

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

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, entity)
    def blackbox(self, entity):
        """Blackboxes all instances of an entity/module"""
        logger.trace(f'blackboxing entity: {entity}')
        self.blackboxes.append(entity)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, instance)
    def blackbox_instance(self, instance):
        """Blackboxes a specific instance of an entity/module"""
        logger.trace(f'blackboxing instance: {instance}')
        self.blackbox_instances.append(instance)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, ...and the rest)
    def cutpoint(self, signal, module=None, resetval=None, condition=None,
                 driver=None, wildcards_dont_match_hierarchy_separators=False):
        """Sets a specifig signal as a cutpoint"""
        cutpoint = {key: value for key, value in locals().items() if key != 'self'}
        logger.trace(f'adding cutpoint: {cutpoint}')
        self.cutpoints.append(cutpoint)

    def run(self, skip_setup=False):
        """Run everything"""
        self.init_results()

        self.start_time_setup = datetime.now().isoformat()
        # TODO: correctly manage self.list here (self.list is True if -l or
        # --list was provided as a command-line argument)

        logger.info(f'Designs: {self.toplevel}')
        for design in self.toplevel:
            logger.info(f'Running {design=}')
            if self.list:
                self.list_design(design)
            else:
                self.run_design(design, skip_setup)

        reports.pretty_summary(self, logger)
        reports.generate_reports(self, logger)
        reports.generate_allure(self, logger)
        err = self.check_errors()
        if err :
          self.exit_if_required(CHECK_FAILED)

    def setup(self):
        for design in self.toplevel:
            if design in self.design_configs:
                logger.trace(f'{design=} has configs: {self.design_configs}')
                for config in self.design_configs[design]:
                    self.setup_design(design, config)
            else:
                logger.trace(f'{design=} has no configs, setting up default config')
                self.setup_design(design, None)

    def list_design(self, design, skip_setup=False):
        """List all available/selected methodology steps for a design"""
        # If configurations exist, list them all
        logger.info(f'Listing {design=} with configs: {self.design_configs}')
        if design in self.design_configs:
            logger.trace(f'{design=} has configs: {self.design_configs}')
            for config in self.design_configs[design]:
                self.list_configuration(design, config)
        else:
            logger.trace(f'{design=} has no configs, running default config')
            self.list_configuration(design, None)

    def run_design(self, design, skip_setup=False):
        """Run all available/selected methodology steps for a design"""
        # If configurations exist, run them all
        logger.info(f'Running {design=} with configs: {self.design_configs}')
        if design in self.design_configs:
            logger.trace(f'{design=} has configs: {self.design_configs}')
            for config in self.design_configs[design]:
                self.run_configuration(design, config, skip_setup)
        else:
            logger.trace(f'{design=} has no configs, running default config')
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
                    logger.trace(f'{step=} of {design=} skipped by skip() function, will not list')
                    self.results[design][step]['status'] = 'skip'
                elif step in toolchains.TOOLS[self.toolchain]:
                    self.list_step(design, step)
                else:
                    logger.trace(f'{step=} not available in {self.toolchain=}, skipping')
                    self.results[design][step]['status'] = 'skip'
        else:
            self.list_step(design, self.step)

    def list_step(self, design, step):
        logger.trace(f'{design}.{step}')
        self.results[design][step]['status'] = 'skip'

    def run_configuration(self, design, config=None, skip_setup=False):
        """Run all available/selected methodology steps for a design
        configuration"""
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
            logger.info(self.steps.steps)
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
                    logger.info(f'{step=} of {design=} skipped by skip() function, will not run')
                    self.results[design][step]['status'] = 'skip'
                # TODO : we probably don't really need TOOLS, since now steps
                # are registered by the toolchain
                elif step in toolchains.TOOLS[self.toolchain]:
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
            reports.pretty_summary(self, logger)
            reports.generate_reports(self, logger)
            reports.generate_allure(self, logger)
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
        logger.info(f'command: {" ".join(cmd)}, working directory: {cwd_for_debug}')

        timestamp = datetime.now().isoformat()
        self.results[design][step]['timestamp'] = timestamp

        start_time = time.perf_counter()
        process = subprocess.Popen (
                  cmd,
                  cwd     = cwd,
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

        self.results[design][step]['stdout'] += captured_stdout
        self.results[design][step]['stderr'] += captured_stderr

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
            logger.error(f'{hook=} is not callable, only functions or other callable objects can be passed as hooks')

    def setup_design(self, design, config = None):
        """Create the output directory and the scripts for a design, but do not
        run anything"""
        # Create the output directories, but do not throw an error if it already
        # exists
        os.makedirs(self.outdir, exist_ok=True)
        self.current_toplevel = design

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
            #logger.trace(f'Setting up {design=}, {step=}')
            self.steps.steps[step]["setup"](self, path)

    def logcheck(self, result, design, step, tool):
        """Check log for errors"""

        # Set the specific log format for this design, step and tool
        self.set_logformat(getlogformattool(design, step, tool))

        # Temporarily add a handler to capture logs
        log_stream = StringIO()
        handler_id = logger.add(log_stream, format="{time} {level} {message}")

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
                    logger.error(f'ERROR detected in {step=}, {tool=}, {line=}')
                err_in_log = True
            elif warn :
                if not self.verbose:
                    logger.warning(f'WARNING detected in {step=}, {tool=}, {line=}')
            elif success :
                if not self.verbose:
                    logger.success(f'SUCCESS detected in {step=}, {tool=}, {line=}')

        # Capture the messages into the results
        self.results[design][step]['message'] += log_stream.getvalue()

        # Remove the handler to stop capturing messages
        logger.remove(handler_id)
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

    # ******************************************************************* #
    # ******************************************************************* #
    # From now on, these are (or should be!) the functions that are
    # toolchain-dependent (meaning that they have tool-specific code)
    # ******************************************************************* #
    # ******************************************************************* #

    # The first two functions, run_step and run_post_step, have a mix of
    # generic and questa-specific code

    # This is part generic and part questa-specific
    # TODO : we have some duplicated code in the way we run commands, becase
    # the code sort of repeats for the GUI invocations. We must see how we can
    # deduplicate this so this function does not get unwieldy
    def run_step(self, design, step):
        """Run a specific step of the methodology"""
        console.rule(f'[bold white]{design}.{step}[/bold white]')
        err = False
        path = self.current_path
        open_gui = False
        # TODO : quick hack to prototype sby support since we cannot change the
        # questa-dependent code (well we can, but we have no way of checking if
        # we broke it since our license is expired)
        if self.toolchain == 'sby':
            if step in self.steps.steps:
                run_stdout, run_stderr = self.steps.steps[step]["run"](self, path)
                logfile = f'{path}/{step}.log'
                logger.info(f'{step=}, finished, output written to {logfile}')
                with open(logfile, 'w') as f :
                    f.write(run_stdout)
                    f.write(run_stderr)
        # If called with a specific step, run that specific step
        # TODO : questa code should also register its run functions with the
        # steps class
        elif step in toolchains.TOOLS[self.toolchain] :
            tool = toolchains.TOOLS[self.toolchain][step][0]
            wrapper = toolchains.TOOLS[self.toolchain][step][1]
            #logger.info(f'{step=}, running {tool=} with {wrapper=}')
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

                    # Parse lint summary here,
                    # maybe we shouldn't do it here
                    if step == 'lint' :
                        lint_rpt_path = f'{self.outdir}/{design}/lint.rpt'
                        if os.path.exists(lint_rpt_path):
                            self.lint_summary = parse_lint.parse_check_summary(lint_rpt_path)
                    # Parse rulecheck summary here,
                    # maybe we shouldn't do it here
                    if step == 'rulecheck' :
                        rulecheck_rpt_path = f'{self.outdir}/{design}/autocheck_verify.rpt'
                        if os.path.exists(rulecheck_rpt_path):
                            self.rulecheck_summary = parse_rulecheck.parse_type_and_severity(rulecheck_rpt_path)
                    # Parse xverify summary here,
                    # maybe we shouldn't do it here
                    if step == 'xverify' :
                        xverify_rpt_path = f'{self.outdir}/{design}/xcheck_verify.rpt'
                        if os.path.exists(xverify_rpt_path):
                            self.xverify_summary = parse_xverify.parse_type_and_result(xverify_rpt_path)
                    # Parse fault summary here,
                    # maybe we shouldn't do it here
                    if step == 'fault' :
                        fault_rpt_path = f'{self.outdir}/{design}/slec_verify.rpt'
                        if os.path.exists(fault_rpt_path):
                            self.fault_summary = parse_fault.parse_fault_summary(fault_rpt_path)
                    # Parse resets summary here,
                    # maybe we shouldn't do it here
                    if step == 'resets' :
                        resets_rpt_path = f'{self.outdir}/{design}/rdc.rpt'
                        if os.path.exists(resets_rpt_path):
                            self.resets_summary = parse_resets.parse_resets_results(resets_rpt_path)
                    # Parse clocks summary here,
                    # maybe we shouldn't do it here
                    if step == 'clocks' :
                        clocks_rpt_path = f'{self.outdir}/{design}/cdc.rpt'
                        if os.path.exists(clocks_rpt_path):
                            self.clocks_summary = parse_clocks.parse_clocks_results(clocks_rpt_path)
                    # Parse property summary here,
                    # maybe we shouldn't do it here
                    if step == 'prove' :
                        prove_rpt_path = f'{self.outdir}/{design}/formal_verify.rpt'
                        if os.path.exists(prove_rpt_path):
                            self.property_summary = generate_test_cases.property_summary(prove_rpt_path)

                    # Parse reachability summary here,
                    # maybe we shouldn't do it here.
                    # Maybe we should delete previous covercheck_verify.rpt?
                    if step == 'reachability':
                        reachability_rpt_path = f'{self.outdir}/{design}/covercheck_verify.rpt'
                        reachability_html_path = f'{self.outdir}/{design}/reachability.html'
                        if os.path.exists(reachability_rpt_path):
                            parse_reports.parse_reachability_report_to_html(reachability_rpt_path, reachability_html_path)
                            reachability_html = reachability_html_path
                        else:
                            reachability_html = None 
                        if reachability_html is not None:
                            with open(reachability_html, 'r', encoding='utf-8') as f:
                                html_content = f.read()

                            tables = parse_reachability.parse_single_table(html_content)
                            self.reachability_summary = parse_reachability.add_total_row(tables)
                    logfile = f'{path}/{step}.log'
                    logger.info(f'{step=}, {tool=}, finished, output written to {logfile}')
                    with open(logfile, 'w') as f :
                        f.write(cmd_stdout)
                        f.write(cmd_stderr)
                    # We cannot exit here immediately because then we wouldn't
                    # be able to open the GUI if there is any error, but we can
                    # record the error and propagate it outside the function
                    if stdout_err or stderr_err:
                        if self.is_failure_allowed(design, step) == False:
                            err = True
                    if stdout_err or stderr_err:
                        if self.is_failure_allowed(design, step) == False:
                            self.results[design][step]['status'] = 'fail'
                        else:
                            self.results[design][step]['status'] = 'broken'
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

    # This is part generic and part questa-specific
    # TODO : sometimes we use design, sometime we use self.current_toplevel. I
    # think maybe we don't need self.current_toplevel and can use design
    # everywhere, or at least inside this function
    def run_post_step(self, design, step):
        """Run post processing for a specific step of the methodology"""
        # Currently we only do post-processing after the friendliness and prove
        # steps
        logger.trace(f'run_post_step, {design=}, {step=})')
        path = self.current_path
        # TODO : quick hack to prototype sby support since we cannot change the
        # questa-dependent code (well we can, but we have no way of checking if
        # we broke it since our license is expired)
        # TODO : run_post_step should probably run a _single_ step, and maybe
        # we can have a run_post_steps function that calls run_post_step
        # multiple times?
        if self.toolchain == 'sby':
            if step in self.steps.post_steps:
                for post_step in self.steps.post_steps[step]:
                    run_stdout, run_stderr = self.steps.steps[step]["run"](self, path)
                    logfile = f'{path}/{step}.log'
                    logger.info(f'{step}.{post_step}, finished, output written to {logfile}')
                    with open(logfile, 'w') as f :
                        f.write(run_stdout)
                        f.write(run_stderr)
            # TODO : correctly process errors
            err = False
        # TODO : questa code should also register the setup/run functions with
        # the steps class and use the same loop as sby
        elif self.toolchain == 'questa':
            if step == 'friendliness':
                rpt = path+'/autocheck_design.rpt'
                data = data_from_design_summary(rpt)
                self.results[design][step]['data'] = data
                self.results[design][step]['score'] = friendliness_score(data)
            if step == 'prove' and self.is_skipped(design, 'prove.formalcover'):
                self.results[design]['prove.formalcover']['status'] = 'skip'
            if step == 'prove' and not self.is_skipped(design, 'prove.formalcover'):
                console.rule(f'[bold white]{design}.prove.formalcover[/bold white]')
                property_summary = generate_test_cases.parse_property_summary(f'{path}/prove.log')
                inconclusives = property_summary.get('Assertions', {}).get('Inconclusive', 0)
                with open(f"{path}/prove_formalcover.do", "w") as f:
                    print('onerror exit', file=f)
                    print(f"formal load db {path}/propcheck.db",file=f)
                    if not self.is_disabled('observability'):
                        print('formal generate coverage -detail_all -cov_mode o', file=f)
                    if not self.is_disabled('reachability'):
                        print(f'formal verify {self.get_tool_flags("formal verify")} -cov_mode reachability', file=f)
                        print('formal generate coverage -detail_all -cov_mode r', file=f)
                    if not self.is_disabled('bounded_reachability') and inconclusives != 0:
                        print(f'formal verify {self.get_tool_flags("formal verify")} -cov_mode bounded_reachability', file=f)
                        print('formal generate coverage -detail_all -cov_mode b', file=f)
                    if not self.is_disabled('signoff'):
                        print(f'formal verify {self.get_tool_flags("formal verify")} -cov_mode signoff', file=f)
                        print('formal generate coverage -detail_all -cov_mode s', file=f)
                    print('', file=f)
                    print('exit', file=f)
                tool = toolchains.TOOLS[self.toolchain][step][0]
                wrapper = toolchains.TOOLS[self.toolchain][step][1]
                logger.info(f'prove.simcover, running {tool=} with {wrapper=}')
                logger.debug(f'Running {tool=} with {wrapper=}')
                if self.toolchain == "questa":
                    cmd = [wrapper, '-c', '-od', path, '-do', f'{path}/prove_formalcover.do']
                    if self.list == True :
                        logger.info(f'Available step: prove.formalcover. Tool: {tool}, command = {" ".join(cmd)}')
                    else :
                        logger.trace(f'command: {" ".join(cmd)=}')
                        cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, 'prove.formalcover', tool, self.verbose)
                        stdout_err = self.logcheck(cmd_stdout, design, 'prove.formalcover', tool)
                        stderr_err = self.logcheck(cmd_stderr, design, 'prove.formalcover', tool)
                        logfile = f'{path}/prove_formalcover.log'
                        logger.info(f'prove.formalcover, {tool=}, finished, output written to {logfile}')
                        with open(logfile, 'w') as f :
                            f.write(cmd_stdout)
                            f.write(cmd_stderr)
                        if stdout_err or stderr_err:
                            if self.is_failure_allowed(design, 'prove.formalcover') == False:
                                err = True
                        if stdout_err or stderr_err:
                            if self.is_failure_allowed(design, 'prove.formalcover') == False:
                                self.results[design]['prove.formalcover']['status'] = 'fail'
                            else:
                                self.results[design]['prove.formalcover']['status'] = 'broken'
                        else:
                            self.results[design]['prove.formalcover']['status'] = 'pass'

                if not self.is_disabled('signoff'):
                    formal_signoff_rpt_path = f'{path}/formal_signoff.rpt'
                    formal_signoff_html_path = f'{path}/formal_signoff.html'
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
                            self.formalcover_summary = parse_formal_signoff.add_total_field(filtered_tables[0])
                            formalcover_summary = self.formalcover_summary
                            goal_percentages = {
                                "Branch": 0.0,
                                "Condition": 0.0,
                                "Expression": 0.0,
                                "FSM State": 0.0,
                                "FSM Transition": 0.0,
                                "Statement": 0.0,
                                "Toggle": 0.0,
                                "Covergroup Bin": 0.0,
                                "Total": 0.0,
                            }

                            formalcover_console = Console(force_terminal=True, force_interactive=False,
                                                    record=True)
                            table = Table(title=f"[cyan]{formalcover_summary['title']}[/cyan]")

                            table.add_column("Status", style="bold")
                            table.add_column("Coverage Type", style="cyan")
                            table.add_column("Total", justify="right")
                            table.add_column("Uncovered", justify="right")
                            table.add_column("Excluded", justify="right")
                            table.add_column("Covered (P)", justify="right")
                            table.add_column("Goal (%)", justify="right")

                            fail_found = False

                            for entry in formalcover_summary["data"]:
                                coverage_type = entry["Coverage Type"]
                                covered_text = entry["Covered (P)"].split("(")[-1].strip(" %)")

                                if covered_text == "N/A":
                                    status = "[white]omit[/white]"
                                    covered_display = f"[bold white]{entry['Covered (P)']}[/bold white]"
                                    covered_percentage = 0.0
                                    goal = 0.0
                                else:
                                    covered_percentage = float(covered_text)
                                    goal = goal_percentages.get(coverage_type, 0.0)

                                    if covered_percentage >= goal:
                                        status = "[green]pass[/green]"
                                        covered_display = f"[bold green]{entry['Covered (P)']}[/bold green]"
                                    else:
                                        status = "[red]fail[/red]"
                                        covered_display = f"[bold red]{entry['Covered (P)']}[/bold red]"
                                        fail_found = True

                                table.add_row(
                                    status,
                                    coverage_type,
                                    str(entry.get("Total","0")),
                                    str(entry.get("Uncovered","0")),
                                    str(entry.get("Excluded", "0")),
                                    covered_display,
                                    f"{goal:.1f}%",
                                )

                            self.results[design]['prove.formalcover']['status'] = "fail" if fail_found else "pass"
                            formalcover_console.print(table)
            # TODO: consider how we are going to present this simcover post_step:
            # is it a step? a post_step?
            # TODO: this needs a refactor but unfortunately I don't have the time
            # for that now :(
            if step == 'prove' and self.is_skipped(design, 'prove.simcover'):
                self.results[design]['prove.simcover']['status'] = 'skip'
            if step == 'prove' and not self.is_skipped(design, 'prove.simcover'):
                console.rule(f'[bold white]{design}.prove.simcover[/bold white]')
                # TODO: encapsulate this in a separate function call
                # TODO: check errors in every call instead of summing everything
                # and just checking at the end (hopefully without copying the code
                # in three different places)
                # TODO: try to deduplicate some of the code
                # TODO: append all the logs to the same message so it appears in
                # the reports, and not only the last log (vcover report)
                stdout_err = 0
                stderr_err = 0
                replay_files = glob.glob(self.outdir+'/'+design+'/qsim_tb/*/replay.vsim.do')
                logger.trace(f'{replay_files=}')
                ucdb_files = list()
                elapsed_time = 0
                timestamp = None
                for file in replay_files:
                    # Modify the replay.vsim.do so:
                    #   - It dumps the waveforms into a .vcd file
                    #   - It specifies a unique test name so we don't get errors when
                    #      merging the UCDBs, and
                    #   - It saves a UCDB file
                    helpers.insert_line_after_target(file, "onerror {resume}", f'vcd dumpports -in -out *')
                    helpers.insert_line_before_target(file, "quit -f;", f'coverage attribute -name TESTNAME -value {pathlib.Path(file).parent.name}')
                    helpers.insert_line_before_target(file, "quit -f;", "coverage save sim.ucdb")
                    # TODO: Maybe we need to modify the replay.scr so it exports
                    # more types of code coverage, we will know that when we try
                    # bigger circuits
                    # Run the replay script
                    path = pathlib.Path(file).parent
                    cmd = ['./replay.scr']
                    cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, f'{step}.simcover', 'vsim', self.verbose, path)
                    elapsed_time += self.results[design][f'{step}.simcover']['elapsed_time']
                    if timestamp is None:
                        timestamp = self.results[design][f'{step}.simcover']['timestamp']
                    # TODO : maybe check for errors here?
                    tool = 'vsim'
                    stdout_err += self.logcheck(cmd_stdout, design, f'{step}.simcover', tool)
                    stderr_err += self.logcheck(cmd_stderr, design, f'{step}.simcover', tool)
                    ucdb_files.append(f'{path}/sim.ucdb')
                # Merge all simulation code coverage
                path = None
                cmd = ['vcover', 'merge', '-out', f'{self.outdir}/{design}/simcover.ucdb']
                cmd = cmd + ucdb_files
                logger.info(f'{cmd=}, {path=}')
                cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, f'{step}.simcover', 'vcover merge', self.verbose, path)
                elapsed_time += self.results[design][f'{step}.simcover']['elapsed_time']
                if timestamp is None:
                    timestamp = self.results[design][f'{step}.simcover']['timestamp']
                # TODO : maybe check for errors here?
                tool = 'vcover'
                stdout_err += self.logcheck(cmd_stdout, design, f'{step}.simcover', tool)
                stderr_err += self.logcheck(cmd_stderr, design, f'{step}.simcover', tool)

                # Check for errors
                err = False
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        err = True
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        self.results[design][f'{step}.simcover']['status'] = 'fail'
                    else:
                        self.results[design][f'{step}.simcover']['status'] = 'broken'

                # Generate simcover summary
                path = f'{self.outdir}/{design}'
                cmd = ['vcover', 'report', '-csv', '-hierarchical', 'simcover.ucdb',
                       '-output', 'simulation_coverage.log']
                cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, f'{step}.simcover', 'vcover report', self.verbose, path)
                elapsed_time += self.results[design][f'{step}.simcover']['elapsed_time']
                self.results[design][f'{step}.simcover']['timestamp'] = timestamp
                self.results[design][f'{step}.simcover']['elapsed_time'] = elapsed_time
                tool = 'vcover'
                stdout_err += self.logcheck(cmd_stdout, design, f'{step}.simcover', tool)
                stderr_err += self.logcheck(cmd_stderr, design, f'{step}.simcover', tool)

                # Check for errors
                err = False
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        err = True
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        self.results[design][f'{step}.simcover']['status'] = 'fail'
                    else:
                        self.results[design][f'{step}.simcover']['status'] = 'broken'
                else:
                    self.results[design][f'{step}.simcover']['status'] = 'pass'

                coverage_data = parse_simcover.parse_coverage_report(f'{path}/simulation_coverage.log')
                self.simcover_summary = parse_simcover.sum_coverage_data(coverage_data)

                # Generate an html report
                path = f'{self.outdir}/{design}'
                cmd = ['vcover', 'report', '-html', '-annotate', '-details',
                       '-testdetails', '-codeAll', '-multibitverbose', '-out',
                       'simcover', 'simcover.ucdb']
                cmd_stdout, cmd_stderr = self.run_cmd(cmd, design, f'{step}.simcover', 'vcover report', self.verbose, path)
                elapsed_time += self.results[design][f'{step}.simcover']['elapsed_time']
                self.results[design][f'{step}.simcover']['timestamp'] = timestamp
                self.results[design][f'{step}.simcover']['elapsed_time'] = elapsed_time
                # TODO : maybe check for errors here?
                tool = 'vcover'
                stdout_err += self.logcheck(cmd_stdout, design, f'{step}.simcover', tool)
                stderr_err += self.logcheck(cmd_stderr, design, f'{step}.simcover', tool)
                # TODO : maybe create also a text report, as #141 suggests?

                # Check for errors
                err = False
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        err = True
                if stdout_err or stderr_err:
                    if self.is_failure_allowed(design, 'prove.simcover') == False:
                        self.results[design][f'{step}.simcover']['status'] = 'fail'
                    else:
                        self.results[design][f'{step}.simcover']['status'] = 'broken'
                else:
                    self.results[design][f'{step}.simcover']['status'] = 'pass'

                if self.simcover_summary is not None:
                    simcover_summary = self.simcover_summary
                    goal_percentages = {
                        "Branches": 0.0,
                        "Conditions": 0.0,
                        "Statments": 0.0,
                        "Toggles": 0.0,
                        "Total": 0.0,
                    }

                    simcover_console = Console(force_terminal=True, force_interactive=False,
                                            record=True)
                    table = Table(title=f"[cyan]Simulation Coverage Summary for Design: {design} [/cyan]")

                    table.add_column("Status", style="bold")
                    table.add_column("Coverage Type", style="cyan")
                    table.add_column("Covered", justify="right")
                    table.add_column("Total", justify="right")
                    table.add_column("Percentage", justify="right")
                    table.add_column("Goal (%)", justify="right")

                    fail_found = False

                    for coverage_type, values in simcover_summary.items():
                        covered = values["covered"]
                        total = values["total"]
                        percentage_text = values["percentage"].strip("%")
                        covered_percentage = float(percentage_text)
                        goal = goal_percentages.get(coverage_type, 0.0)

                        if covered_percentage >= goal:
                            status = "[green]pass[/green]"
                            percentage_display = f"[bold green]{values['percentage']}[/bold green]"
                        else:
                            status = "[red]fail[/red]"
                            percentage_display = f"[bold red]{values['percentage']}[/bold red]"
                            fail_found = True

                        table.add_row(
                            status,
                            coverage_type,
                            str(covered),
                            str(total),
                            percentage_display,
                            f"{goal:.1f}%",
                        )

                    self.results[design]['prove.simcover']['status'] = "fail" if fail_found else "pass"
                    simcover_console.print(table)

        return err

    # This is questa-specific
    def generics_to_args(self, generics):
        """Converts a dict with generic:value pairs to the argument we have to
        pass to the tools"""
        string = ''
        for i in generics:
            string += f'-g {i}={generics[i]} '
        return string

    # This is questa-specific
    def timeout(self, step, timeout):
        """Set the timeout for a specific step"""
        timeout_value = f" -timeout {timeout} "
        if step == "rulecheck":
            self.tool_flags["autocheck verify"] += timeout_value
        elif step == "xverify":
            self.tool_flags["xcheck verify"] += timeout_value
        elif step == "reachability":
            self.tool_flags["covercheck verify"] += timeout_value
        elif step == "prove":
            self.tool_flags["formal verify"] += timeout_value

    # This is questa-specific
    def add_external_library(self, name, src):
        """Add an external library"""
        logger.info(f'Adding the external library: {name} from {src}')
        if not os.path.exists(src) :
            logger.error(f'External library not found: {name} from {src}')
            self.exit_if_required(BAD_VALUE)
        try:
            logger.info(f'Compiling library {name} from {src}')
            self.run_command(f'vlib {name}')
            self.run_command(f'vmap {name} {name}')
            vhdl_files = [os.path.join(root, file) 
                        for root, _, files in os.walk(src) 
                        for file in files if file.endswith(('.vhd', '.VHD', '.vhdl', '.VHDL'))]
            if vhdl_files:
                logger.info(f'Compiling VHDL files for external library {name}')
                self.run_command(f'vcom -work {name} -{self.vhdlstd} -autoorder {" ".join(vhdl_files)}')
        except Exception as e:
            logger.error(f'Error compiling library {name}: {e}')
            self.exit_if_required(BAD_VALUE)
        logger.info(f'Successfully added and mapped library {name}')

    # This is questa-specific
    def add_precompiled_library(self, name, path):
        """Add a precompiled external library"""
        logger.info(f'Adding precompiled library: {name} from {path}')
        if not os.path.exists(path):
            logger.error(f'Precompiled library path not found: {path}')
            self.exit_if_required(BAD_VALUE)
        try:
            logger.info(f'Mapping precompiled library {name} to {path}')
            self.run_command(f'vmap {name} {path}')
        except Exception as e:
            logger.error(f'Error mapping precompiled library {name}: {e}')
            self.exit_if_required(BAD_VALUE)
        logger.info(f'Successfully mapped precompiled library {name}')

    # This is questa-specific
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

    # This is questa-specific
    def check_library_exists(self, path) :
        if self.toolchain == "questa" :
            expectedfile = path + "_info"
        logger.debug(f'checking if {expectedfile=} exists')
        if os.path.exists(path) :
            ret = True
        else :
            ret = False
        return ret

    # This is questa-specific
    def cmd_create_library(self, lib):
        if self.toolchain == "questa":
            cmd = toolchains.TOOLS[self.toolchain]["createemptylib"] + ' ' + lib
        return cmd

