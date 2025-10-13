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
import signal
from datetime import datetime
from io import StringIO
from shlex import join

# Third party imports
import argparse
from loguru import logger
from rich.console import Console

# Our own imports
from fvm import logcounter
from fvm import helpers
from fvm import reports
from fvm.steps import steps
from fvm.toolchains import toolchains
from fvm.drom2psl.generator import generator

# Error codes
# Error codes 1 and 2 are reserved: 1 is the default error code in unix shells,
# and 2 is sometimes used to signal syntax errors in the executed command
BAD_VALUE = {"msg": "FVM exit condition: Bad value",
             "value" : 3}
ERROR_IN_TOOL = {"msg": "FVM exit condition: Error detected during tool execution",
                 "value": 4}
GOAL_NOT_MET = {"msg": "FVM exit condition: User goal not met",
                "value": 5}
CHECK_FAILED = {"msg": "FVM exit condition: check_for_errors failed",
                "value": 6}
KEYBOARD_INTERRUPT = {"msg": "FVM exit condition: Keyboard interrupt",
                "value": 7}

# Log formats
LOGFORMAT = '<cyan>FVM</cyan> | <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
LOGFORMAT_SUMMARY = '<cyan>FVM</cyan> | <green>Summary</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
#LOGFORMAT_TOOL = '<cyan>FVM</cyan> | <green>Tool</green> | <level>{level: <8}</level> | <level>{message}</level>'

def getlogformattool(design, step, tool):
    return f'<cyan>{design}.{step}</cyan> | <green>{tool=}</green> | ' + '<level>{level: <8}</level> | <level>{message}</level>'

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
        self.toplevel = []
        self.current_toplevel = ''
        self.start_time_setup = None
        self.init_reset = []
        self.vhdl_sources = []
        self.libraries_from_vhdl_sources = []
        self.psl_sources = []
        self.drom_sources = []
        self.drom_generated_psl = []
        self.skip_list = []
        self.allow_failure_list = []
        self.disabled_coverage = []
        self.vhdlstd = "2008"
        self.tool_flags = {}
        self.resets = []
        self.clocks = []
        self.reset_domains = []
        self.clock_domains = []
        self.blackboxes = []
        self.blackbox_instances = []
        self.cutpoints = []
        self.pre_hooks = {}
        self.post_hooks = {}
        self.designs = []
        self.design_configs = {}
        self.ctrl_c_pressed = False

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
        toolchains.define_steps(self, self.steps, self.toolchain)
        self.logger.info(f'{steps=}')

        # Exit if args.step is unrecognized
        if args.step is not None:
            if args.step not in self.steps.steps:
                self.logger.error(f'step {args.step} not available in {self.toolchain}. Available steps are: {list(self.steps.steps.keys())}')
                self.exit_if_required(BAD_VALUE)

    def set_toolchain(self, toolchain):
        """
        Override the current toolchain selection.

        This method allows overriding the ``FVM_TOOLCHAIN`` environment variable
        and explicitly setting a different toolchain for the framework. If the
        provided toolchain is not supported, the framework logs an error and exits.

        :param toolchain: Name of the toolchain to be set.
        :type toolchain: str
        """
        if toolchain not in toolchains.toolchains :
            self.logger.error(f'{toolchain=} not supported')
            self.exit_if_required(BAD_VALUE)
        else :
            self.toolchain = toolchain

    def add_vhdl_source(self, src, library="work"):
        """
        Add a single VHDL source file to the framework.

        This method registers a VHDL source file for later compilation and 
        associates it with a VHDL library (defaulting to ``work``). It checks 
        whether the file exists and validates its extension. Non-standard 
        extensions trigger a warning but are still accepted.

        :param src: Path to the VHDL source file.
        :type src: str
        :param library: VHDL library name to associate with the source file.
                        Defaults to ``"work"``.
        :type library: str
        """
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
        """
        Remove all registered VHDL sources from the framework.

        This method clears the internal list of VHDL sources.
        """
        self.logger.info('Removing all VHDL sources')
        self.vhdl_sources = []

    def add_psl_source(self, src):
        """
        Add a single PSL (Property Specification Language) source file to the framework.

        The function validates that the provided file exists and checks whether
        it has a common PSL extension. If the file does not exist, the framework will
        log an error and exit. If the extension is unusual, a warning is logged.

        :param src: Path to the PSL source file.
        :type src: str
        """
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
        """
        Remove all registered PSL sources from the framework.

        This method clears the internal list of PSL sources.
        """
        self.logger.info('Removing all PSL sources')
        self.psl_sources = []

    def add_drom_source(self, src):
        """
        Add a single Wavedrom source file to the framework.

        This method validates that the provided file exists and checks whether
        it has a typical Wavedrom extension (``.json``, ``.JSON``, ``.drom``, or ``.wavedrom``).
        If the file does not exist, the framework logs an error and exits.
        If the extension is unusual, a warning is logged.

        :param src: Path to the Wavedrom source file.
        :type src: str
        """
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
        """
        Remove all registered Wavedrom sources from the framework.

        This method clears the internal list of Wavedrom sources.
        """
        self.logger.info('Removing all wavedrom sources')
        self.drom_sources = []

    def add_vhdl_sources(self, globstr, library="work"):
        """
        Add multiple VHDL source files to the framework using a glob pattern.

        This method searches for all files matching the provided glob pattern 
        and adds them as VHDL sources. Each matching file is added via 
        :meth:`add_vhdl_source`. If no files match the pattern, an error is
        logged and the framework exits.

        :param globstr: Glob pattern to search for VHDL source files.
        :type globstr: str
        :param library: VHDL library name to associate with the sources. Defaults 
                        to ``"work"``.
        :type library: str
        """
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_vhdl_source(source, library)

    def add_psl_sources(self, globstr):
        """
        Add multiple PSL source files to the framework using a glob pattern.

        This method searches for all files matching the provided glob pattern 
        and adds them as PSL sources. Each matching file is added via 
        :meth:`add_psl_source`. If no files match the pattern, an error is
        logged and the framework exits.

        :param globstr: Glob pattern to search for PSL source files.
        :type globstr: str
        """
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_psl_source(source)

    def add_drom_sources(self, globstr):
        """
        Add multiple Wavedrom source files to the framework using a glob pattern.

        This method searches for all files matching the provided glob pattern 
        and adds them as Wavedrom sources. Each matching file is added via 
        :meth:`add_drom_source`. If no files match the pattern, an error is
        logged and the framework exits.

        :param globstr: Glob pattern to search for Wavedrom source files.
        :type globstr: str
        """
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            self.logger.error(f'No files found for pattern {globstr}')
            self.exit_if_required(BAD_VALUE)
        for source in sources:
            self.add_drom_source(source)

    def list_vhdl_sources(self):
        """
        List all VHDL source files in the framework.

        This method logs the current list of VHDL source files stored in the 
        framework.
        """
        self.logger.info(f'{self.vhdl_sources=}')

    def list_psl_sources(self):
        """
        List all PSL source files in the framework.

        This method logs the current list of PSL source files stored in the 
        framework.
        """
        self.logger.info(f'{self.psl_sources=}')

    def list_drom_sources(self):
        """
        List all Wavedrom source files in the framework.

        This method logs the current list of Wavedrom source files stored in the 
        framework.
        """
        self.logger.info(f'{self.drom_sources=}')

    def list_sources(self):
        """
        List all source files in the framework.

        This method logs all sources currently added to the framework, including:

        - VHDL sources
        - PSL sources
        - Wavedrom sources
        """
        self.list_vhdl_sources()
        self.list_psl_sources()
        self.list_drom_sources()

    def check_tool(self, tool):
        """
        Check whether a tool name is available in the system PATH.

        This method searches for the specified tool name in the system PATH.
        It logs a warning if the tool is not found, and logs a success
        message if it is found.

        :param tool: Name of the tool name to search for in PATH.
        :type tool: str
        :return: True if the tool is found in PATH, False otherwise.
        :rtype: bool
        """
        path = shutil.which(tool)
        if path is None :
            self.logger.warning(f'{tool=} not found in PATH')
            ret = False
        else :
            self.logger.success(f'{tool=} found at {path=}')
            ret = True
        return ret

    def set_prefix(self, prefix):
        """
        Set the prefix string for the framework.

        The prefix is used to distinguish between different executions of the
        same toplevel in the reports (shows <prefix>.<toplevel>.<config>). This
        method validates that the provided prefix is a string. If the value
        is not a string, an error is logged and the framework exits.

        :param prefix: The prefix string to set.
        :type prefix: str
        """
        if not isinstance(prefix, str):
            self.logger.error(f'Specified {prefix=} is not a string, {type(prefix)=}')
            self.exit_if_required(BAD_VALUE)
        self.prefix = prefix

    def set_toplevel(self, toplevel):
        """
        Set the name of the toplevel module.

        This method allows specifying one or multiple toplevel modules. If a 
        single toplevel module is provided as a string, it is converted into a 
        single-element list. If a list is provided, duplicates are checked and 
        an error is logged if any are found.

        Certain reserved names are prohibited (``fvm_dashboard`` and 
        ``fvm_reports``) to avoid conflicts with framework directories.

        If a specific design has already been set with framework
        argument ``-d``, ``--design``, only that design will be 
        kept in the toplevel list; an error is raised if the design is not 
        present in the provided toplevel list.

        :param toplevel: Name of the toplevel module as a string, or a list of 
                        toplevel module names.
        :type toplevel: str or list of str
        """

        if isinstance(toplevel, str):
            self.toplevel = [toplevel]
        elif isinstance(toplevel, list):
            # Check for duplicates and throw an error if a toplevel is
            # specified more than once
            if len(toplevel) != len(set(toplevel)):
                self.logger.error(f'Duplicates exist in {toplevel=}')
                self.exit_if_required(BAD_VALUE)
            else:
                self.toplevel = toplevel

        # TODO : in the future, the design output dirs may have the library
        # name, such as libname.design or libname/design, so that error message
        # will not be necessary because there won't be any clashes with fvm_*
        # directories
        if 'fvm_dashboard' in toplevel or 'fvm_reports' in toplevel:
            self.logger.error("toplevels can not have the following reserved names: fvm_dashboard, fvm_reports")
            self.exit_if_required(BAD_VALUE)

        # If a design was specified, just run that design
        if self.design is not None:
            if self.design in self.toplevel:
                self.toplevel = [self.design]
            else:
                self.logger.error(f'Specified {self.design=} not in {self.toplevel=}, did you add it with set_toplevel()?')
                self.exit_if_required(BAD_VALUE)

    def init_results(self):
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
            for step in self.steps.steps:
                self.results[design][step] = {}
                self.results[design][step]['message'] = ''
                self.results[design][step]['stdout'] = ''
                self.results[design][step]['stderr'] = ''
                self.results[design][step]['summary'] = {}
                if step in self.steps.post_steps:
                    for post_step in self.steps.post_steps[step]:
                        self.results[design][f'{step}.{post_step}'] = {}
                        self.results[design][f'{step}.{post_step}']['message'] = ''
                        self.results[design][f'{step}.{post_step}']['stdout'] = ''
                        self.results[design][f'{step}.{post_step}']['stderr'] = ''
                        self.results[design][f'{step}.{post_step}']['summary'] = {}

    def add_config(self, design, name, generics):
        """
        Add a design configuration.

        This method registers a configuration for a given design. Each configuration
        has a name and a dictionary with the generics/parameters. Once at least one
        configuration exists for a design, the framework default configuration is not used.

        :param design: Name of the design to which the configuration applies. Must
                    be one of the toplevel modules.
        :type design: str
        :param name: Name of the configuration.
        :type name: str
        :param generics: Dictionary with the generics/parameters for the configuration.
        :type generics: dict
        """

        # Check that the configuration is for a valid design
        if design not in self.toplevel:
            self.logger.error(f'Specified {design=} not in {self.toplevel=}')
            self.exit_if_required(BAD_VALUE)

        # Initialize the design configurations list if it doesn't exist
        if design not in self.design_configs:
            self.design_configs[design] = []

        # Create the configuration as a dict() and append it to the design
        # configurations list
        config = {}
        config["name"] = name
        config["generics"] = generics
        self.design_configs[design].append(config)
        self.logger.trace(f'Added configuration {self.design_configs} to {design=}')

    def skip(self, step, design='*'):
        """
        Allow to skip specific steps.

        Both the step and the design can be specified. The special wildcard '*' can
        be used to indicate all steps or all designs.

        :param step: Name of the step to skip.
        :type step: str
        :param design: Name of the design to skip the step for. Defaults to '*', 
                    which matches all designs.
        :type design: str
        """
        self.skip_list.append(f'{design}.{step}')

    def allow_failure(self, step, design='*'):
        """
        Allow specific steps to fail.

        The fail will be marked but the execution will continue. Both the step and
        the design can be specified. The special wildcard '*' can be used to
        indicate all steps or all designs.

        :param step: Name of the step to allow the fail.
        :type step: str
        :param design: Name of the design to allow the fail for. Defaults to '*', 
                    which matches all designs.
        :type design: str
        """
        self.allow_failure_list.append(f'{design}.{step}')

    def disable_coverage(self, covtype, design='*'):
        """
        Disable specific types of coverage collection for a design or all designs.

        This method allows the user to disable certain coverage types during
        formal coverage. The special wildcard '*' can be used for the
        design parameter to apply the disablement to all designs. If the 
        specified coverage type is not allowed, an error will be logged and the
        framework will exit.

        Allowed coverage types are:

        - ``observability``
        - ``reachability``
        - ``bounded_reachability``
        - ``signoff``

        :param covtype: Type of coverage to disable.
        :type covtype: str
        :param design: Name of the design to disable coverage for. Defaults to '*',
                    which applies to all designs.
        :type design: str
        """
        allowed_covtypes = ['observability', 'signoff', 'reachability', 'bounded_reachability']
        if covtype not in allowed_covtypes :
            self.logger.error(f'Specified {covtype=} not in {allowed_covtypes=}')
            self.exit_if_required(BAD_VALUE)
        self.disabled_coverage.append(f'{design}.prove.{covtype}')

    def set_timeout(self, step, timeout):
        """
        Set the execution timeout for a specific step.

        The timeout specifies the maximum allowed execution time for
        the given step. It may be that the time during the step is slightly
        longer than the timeout because the timeout is for the tool execution,
        but does not take into account the tool compilation. Not all steps
        have a timeout, although if they don't, they probably won't take long.

        The timeout should be provided as a string combining a number and a unit:

        - ``s`` for seconds (e.g., "1s")
        - ``m`` for minutes (e.g., "10m")
        - ``h`` for hours (e.g., "1h")
        - ``d`` for days (e.g., "2d")

        :param step: Name of the step to set the timeout for.
        :type step: str
        :param timeout: Timeout value as a string with a number and unit.
        :type timeout: str
        :return: None
        :rtype: None
        """
        toolchains.set_timeout(self, self.toolchain, step, timeout)

    def set_coverage_goal(self, step, goal):
        """
        Set the coverage goal for a specific step.

        This method allows configuring the target coverage percentage for a
        given step. The goal must be a number between 0 and 100 (inclusive). 

        :param step: Name of the step to set the coverage goal for.
        :type step: str
        :param goal: Coverage goal value, must be between 0 and 100.
        :type goal: int or float
        """
        if not (isinstance(goal, (int, float)) and 0 <= goal <= 100):
            self.logger.error(f"{goal=} must be between 0 and 100")
            self.exit_if_required(BAD_VALUE)

        valid = False
        if step in self.steps.steps:
            valid = True
        elif "." in step:
            prefix, suffix = step.split(".", 1)
            if prefix in self.steps.post_steps and suffix in self.steps.post_steps[prefix]:
                valid = True

        if not valid:
            self.logger.error(f"Specified {step=} not in {self.steps.steps=}"
                              f" or {self.steps.post_steps=}")
            self.exit_if_required(BAD_VALUE)

        toolchains.set_coverage_goal(self.toolchain, step, goal)

    def generics_to_args(self, generics):
        """Converts a dict with generic:value pairs to the argument we have to
        pass to the tools"""
        return toolchains.generics_to_args(self.toolchain, generics)

    def formal_initialize_reset(self, reset, active_high=True, cycles=1):
        """
        Initialize a reset signal for formal steps.

        This method initializes the reset signal in formal when the tool
        cannot infer it. Only formal steps can use it.

        :param reset: Name of the reset signal to initialize.
        :type reset: str
        :param active_high: Whether the reset is active high (True) or
                            active low (False). Defaults to True.
        :type active_high: bool
        :param cycles: Number of cycles the reset should be asserted during
                    initialization. Defaults to 1.
        :type cycles: int
        """
        toolchains.formal_initialize_reset(self, self.toolchain, reset, active_high, cycles)

    def set_pre_hook(self, hook, step, design='*'):
        """
        Register a hook before a specific step.

        A pre-hook is a user-defined callable that will be executed before the
        specified step runs. Hooks can be assigned to a specific design or to
        all designs using the wildcard '*'.

        :param hook: Callable to execute before the step.
        :type hook: callable
        :param step: Name of the step to attach the pre-hook to.
        :type step: str
        :param design: Name of the design to apply the hook to, or '*' to apply
                    to all designs. Defaults to '*'.
        :type design: str
        """
        if design not in self.pre_hooks:
            self.pre_hooks[design] = {}
        self.pre_hooks[design][step] = hook

    def set_post_hook(self, hook, step, design='*'):
        """
        Register a hook after a specific step.

        A post-hook is a user-defined callable that will be executed after the
        specified step runs. Hooks can be assigned to a specific design or to
        all designs using the wildcard '*'.

        :param hook: Callable to execute after the step.
        :type hook: callable
        :param step: Name of the step to attach the post-hook to.
        :type step: str
        :param design: Name of the design to apply the hook to, or '*' to apply
                    to all designs. Defaults to '*'.
        :type design: str
        """
        if design not in self.post_hooks:
            self.post_hooks[design] = {}
        self.post_hooks[design][step] = hook

    def set_loglevel(self, loglevel):
        """
        Set the logging level for the build and test framework.

        This method configures the framework's logger to use the specified
        logging level. Only the levels allowed by loguru are accepted:

        - ``TRACE``
        - ``DEBUG``
        - ``INFO``
        - ``SUCCESS``
        - ``WARNING``
        - ``ERROR``
        - ``CRITICAL``

        :param loglevel: Logging level to set for the framework.
        :type loglevel: str
        """
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
        """
        Log a message from external code using the framework's logger.

        This method allows external scripts or test files to log messages
        through the framework's logging system. The severity level are
        the loguru levels, mentioned in :meth:`set_loglevel`.

        :param severity: Logging level to use. The value is case-insensitive.
        :type severity: str
        :param string: Message text to be logged.
        :type string: str
        """
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

        return ret

    # TODO : check that port_list must be an actual list()
    # TODO : change how this function is used!!!!!!
    # Disable pylint unused-argument warnings because all arguments
    # are used but with locals(), so pylint doesn't see
    # that they are used because it is done dynamically
    # pylint: disable=unused-argument
    def add_clock_domain(self, port_list, clock_name=None, asynchronous=None,
                        ignore=None, posedge=None, negedge=None, module=None,
                        inout_clock_in=None, inout_clock_out=None):
        """
        Add a clock domain definition to the framework.

        This method registers a new clock domain with its associated ports and
        synchronization properties.

        :param port_list: List of ports belonging to the clock domain.
        :type port_list: list[str]
        :param clock_name: Name of the clock. If None, the port domain may be
                        asynchronous or ignored based on other parameters.
        :type clock_name: str or None
        :param asynchronous: Ports that are asynchronous to all clock domains.
                                If clock_name has been specified, the ports are
                                considered asynchronous, but the ports' receiving
                                clock domain is derived from clock_name.
        :type asynchronous: bool or None
        :param ignore: Input ports that should be ignored.
        :type ignore: bool or None
        :param posedge: Clocked by the positive edge of the clock signal. If both ``posedge``
                        and ``negedge`` are specified, both edges of the clock are
                        considered active for this domain. Default: positive edge only.
        :type posedge: bool or None
        :param negedge: Clocked by the negative edge of the clock signal.
        :type negedge: bool or None
        :param module: Optional module name to which the domain belongs.
        :type module: str or None
        :param inout_clock_in: Specify the **input** direction clock domain name for inout ports.
        :type inout_clock_in: bool or None
        :param inout_clock_out: Specify the **output** direction clock domain name for inout ports.
        :type inout_clock_out: bool or None
        """
        domain = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding clock domain: {domain}')
        self.clock_domains.append(domain)

    # TODO : check that port_list must be an actual list()
    def add_reset_domain(self, port_list, name=None, asynchronous=None,
                         synchronous=None, active_high=None, active_low=None,
                         is_set=None, no_reset=None, module=None, ignore=None):
        """
        Adds a reset domain definition to the framework.

        This function registers a new reset domain by specifying the ports that belong to it,
        its name, and various properties such as polarity, synchronization...

        :param port_list: List of ports that belong to the reset domain.
        :type port_list: list[str]
        :param name: Name of the reset domain. If None, the port domain may be
                        ignored or have no reset based on other parameters.
        :type name: str or None
        :param asynchronous: If True, the reset signal is considered asynchronous.
        :type asynchronous: bool or None
        :param synchronous: If True, the reset signal is considered synchronous.
        :type synchronous: bool or None
        :param active_high: If True, the reset signal is active high.
        :type active_high: bool or None
        :param active_low: If True, the reset signal is active low.
        :type active_low: bool or None
        :param is_set: If True, the reset signal behaves as a set-type control instead of reset.
        :type is_set: bool or None
        :param no_reset: If True, indicates the port has no reset control.
        :type no_reset: bool or None
        :param module: Optional module name associated with the reset domain.
        :type module: str or None
        :param ignore: Ports ignored for reset analysis.
        :type ignore: bool or None
        """
        domain = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding reset domain: {domain}')
        self.reset_domains.append(domain)

    def add_reset(self, name, module=None, group=None, active_low=None,
                  active_high=None, asynchronous=None, synchronous=None,
                  external=None, ignore=None, remove=None):
        """
        Add a reset signal to the design.

        This method registers a reset signal. The reset can have various properties
        such as polarity, synchronization, and domain association.

        :param name: Name of the reset signal.
        :type name: str
        :param module: Optional name of the module associated with the reset.
        :type module: str or None
        :param group: Optional reset group name to classify the reset signal.
        :type group: str or None
        :param active_low: If True, the reset signal is active low.
        :type active_low: bool or None
        :param active_high: If True, the reset signal is active high.
        :type active_high: bool or None
        :param asynchronous: If True, the reset signal is considered asynchronous.
        :type asynchronous: bool or None
        :param synchronous: If True, the reset signal is considered synchronous.
        :type synchronous: bool or None
        :param external: If True, the reset signal is considered external.
        :type external: bool or None
        :param ignore: If True, the reset signal is ignored.
        :type ignore: bool or None
        :param remove: If True, the inferred reset signal is removed.
        :type remove: bool or None
        """
        # Copy all arguments to a dict, excepting self
        reset = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding reset: {reset}')
        self.resets.append(reset)

    def add_clock(self, name, module=None, group=None, period=None,
                  waveform=None, external=None, ignore=False, remove=False):
        """
        Add a clock signal to the design.

        This method registers a clock. The clock can have various properties
        such as period, waveform, domain association, and external status.

        :param name: Name of the clock signal.
        :type name: str
        :param module: Optional module name associated with the clock.
        :type module: str or None
        :param group: Optional clock group name to classify the clock signal.
        :type group: str or None
        :param period: Clock period in ns.
        :type period: float or int or None
        :param waveform:
            Clock waveform definition, a tuple (rise_time, fall_time) 
            to define duty cycle. If period is 10, default waveform is (0, 5),
            i. e. a 50% duty cycle.
        :type waveform: tuple[float, float] or tuple[int, int] or None
        :param external: Indicates that the clock comes from an external source.
        :type external: bool or None
        :param ignore: If True, this clock will be ignored.
        :type ignore: bool or None
        :param remove: If True, this clock will be removed.
        :type remove: bool or None
        """
        clock = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding clock: {clock}')
        self.clocks.append(clock)
    # pylint: enable=unused-argument

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, entity)
    def blackbox(self, entity):
        """
        Blackboxes all instances of a given entity or module.

        :param entity: Name of the entity or module to be blackboxed.
        :type entity: str
        """
        self.logger.trace(f'blackboxing entity: {entity}')
        self.blackboxes.append(entity)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, instance)
    def blackbox_instance(self, instance):
        """
        Blackboxes a specific instance of a given entity or module.

        :param instance: Name of the instance to be blackboxed.
        :type instance: str
        """
        self.logger.trace(f'blackboxing instance: {instance}')
        self.blackbox_instances.append(instance)

    # TODO : consider what happens when we have multiple toplevels, maybe we
    # should have the arguments (self, design/toplevel, ...and the rest)
    # pylint: disable=unused-argument
    def cutpoint(self, signal, module=None, resetval=None, condition=None,
                 driver=None, wildcards_dont_match_hierarchy_separators=False):
        """
        Define a cutpoint on a specific signal in the design.

        :param signal: Name of the signal to mark as a cutpoint.
        :type signal: str
        :param module: Optional module name that contains the signal.
        :type module: str or None
        :param resetval: If True, the cutpoint will take the reset value.
        :type resetval: bool or None
        :param driver: Optional signal or port driving this cutpoint.
        :type driver: str or None
        :param condition: Optional condition expression under which the cutpoint is active.
        :type condition: str or None
        :param wildcards_dont_match_hierarchy_separators:
            If True, wildcard patterns in `signal` names will not match
            hierarchy separators (typically '.').
        :type wildcards_dont_match_hierarchy_separators: bool
        """
        cutpoint = {key: value for key, value in locals().items() if key != 'self'}
        self.logger.trace(f'adding cutpoint: {cutpoint}')
        self.cutpoints.append(cutpoint)
    # pylint: enable=unused-argument

    def run(self, skip_setup=False):
        """
        Execute the full flow of the framework for all specified toplevels.

        This method run the framework and, optionally, skips the setup phase,
        resulting in the use of existing scripts, which can be defined manually
        or generated in a previous run.

        :param skip_setup: If True, the setup is skipped and existing scripts are used.
        :type skip_setup: bool
        """
        self.init_results()

        self.start_time_setup = datetime.now().isoformat()

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
        reports.generate_md(self)
        err = self.check_errors()
        if err :
            self.exit_if_required(CHECK_FAILED)

    def list_design(self, design):
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
            for step in self.steps.steps:
                if self.is_skipped(design, step):
                    self.logger.trace(f'{step=} of {design=} skipped by skip() function, will not list')
                    self.results[design][step]['status'] = 'skip'
                else:
                    self.list_step(design, step)
                    for post_step in self.steps.post_steps.get(step, []):
                        self.list_step(design, f'{step}.{post_step}')
        else:
            self.list_step(design, self.step)
            for post_step in self.steps.post_steps.get(self.step, []):
                self.list_step(design, f'{self.step}.{post_step}')

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
                shutil.copytree(current_dir, target_dir)
                for item in os.listdir(current_dir):
                    path = os.path.join(current_dir, item)
                    if os.path.isdir(path):
                        shutil.rmtree(path)

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
            for step in self.steps.steps:
                if self.is_skipped(design, step):
                    self.logger.info(f'{step=} of {design=} skipped by skip() function, will not run')
                    self.results[design][step]['status'] = 'skip'
                else:
                    # TODO : allow pre_hooks to return errors and stop the run
                    # if they fail
                    self.run_pre_hook(design, step)
                    err, errorcode = self.run_step(design, step)
                    if err:
                        self.exit_if_required(errorcode)
                    err, errorcode = self.run_post_step(design, step)
                    if err:
                        self.exit_if_required(errorcode)
                    # TODO : allow post_hooks to return errors and stop the run
                    # if they fail
                    self.run_post_hook(design, step)
        else:
            self.run_pre_hook(design, self.step)
            err, errorcode = self.run_step(design, self.step)
            if err:
                self.exit_if_required(errorcode)
            err, errorcode = self.run_post_step(design, self.step)
            if err:
                self.exit_if_required(errorcode)
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
        """
        Set user-defined flags for a specific tool.

        These flags will be used when invoking the specified tool during
        the framework flow. This allows customizing tool behavior without
        modifying internal scripts or commands.

        :param tool: Name of the tool to set flags for.
        :type tool: str
        :param flags: Flags to pass to the tool.
        :type flags: str
        """
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

    def exit_if_required(self, errorcode):
        """Exits with a specific error code if the continue flag (cont) is not
        set"""
        if self.cont and self.ctrl_c_pressed is False:
            pass
        else:
            reports.pretty_summary(self, self.logger)
            reports.generate_reports(self, self.logger)
            reports.generate_allure(self, self.logger)
            reports.generate_md(self)
            self.logger.error(errorcode['msg'])
            sys.exit(errorcode['value'])

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

        def handle_sigint(signum, frame):
            self.logger.error("Ctrl+C detected")
            self.ctrl_c_pressed = True
            os.killpg(os.getpgid(process.pid), signal.SIGINT)

        signal.signal(signal.SIGINT, handle_sigint)

        # Initialize variables where to store command stdout/stderr
        stdout_lines = []
        stderr_lines = []

        if not verbose:
            print('Running: ', end='', flush=True)

        # If verbose, read and print stdout and stderr in real-time
        with process.stdout as stdout, process.stderr as stderr:
            for line in iter(stdout.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn, success = self.linecheck(line, step)
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
                    err, warn, success = self.linecheck(line, step)
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

        # Raise an exception if the return code is non-zero and Ctrl+C was
        # not pressed
        if retval != 0 and self.ctrl_c_pressed is False:
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
            err, warn, success = self.linecheck(line, step)

            if self.is_failure_allowed(design, step) is True and err:
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

    def linecheck(self, line, step=None):
        """Check for errors and warnings in log lines"""
        err = False
        warn = False
        success = False
        patterns = toolchains.get_linecheck_patterns(self, step)
        if patterns:
            for keyword in patterns.get("ignore", []):
                if keyword.casefold() in line.casefold():
                    return err, warn, success

            for category, keywords in patterns.items():
                if category == "ignore":
                    continue
                for keyword in keywords:
                    regex = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
                    if regex.search(line):
                        if category == "error":
                            err = True
                        elif category == "warning":
                            warn = True
                        elif category == "success":
                            success = True

        return err, warn, success

    def run_step(self, design, step):
        """Run a specific step of the methodology"""
        console.rule(f'[bold white]{design}.{step}[/bold white]')
        err = False
        errorcode = {}
        self.current_path = f'{self.outdir}/{self.current_toplevel}'
        path = self.current_path
        if step in self.steps.steps:
            run_stdout, run_stderr, stdout_err, stderr_err, status = self.steps.steps[step]["run"](self, path)
            logfile = f'{path}/{step}/{step}.log'
            self.logger.info(f'{step=}, finished, output written to {logfile}')
            with open(logfile, 'w', encoding='utf-8') as f :
                f.write(run_stdout)
                f.write(run_stderr)

            if stdout_err or stderr_err or status == "fail":
                if self.is_failure_allowed(design, step) is False:
                    err = True
                    errorcode = ERROR_IN_TOOL
                self.results[design][step]['status'] = 'fail'
            elif status == "goal_not_met":
                if self.is_failure_allowed(design, step) is False:
                    err = True
                    errorcode = GOAL_NOT_MET
                self.results[design][step]['status'] = 'fail'
            else:
                self.results[design][step]['status'] = 'pass'

        else:
            self.logger.error(f'No tool available for {step=} in {self.toolchain=}')
            self.exit_if_required(BAD_VALUE)

        if self.ctrl_c_pressed is True:
            self.exit_if_required(KEYBOARD_INTERRUPT)

        if err is False and step in self.steps.post_steps:
            for post_step in self.steps.post_steps[step]:
                self.steps.post_steps[step][post_step]["setup"](self, path)

        return err, errorcode

    def run_post_step(self, design, step):
        """Run post processing for a specific step of the methodology"""
        self.logger.trace(f'run_post_step, {design=}, {step=})')
        self.current_path = f'{self.outdir}/{self.current_toplevel}'
        path = self.current_path
        err = False
        errorcode = {}
        if step in self.steps.post_steps:
            for post_step in self.steps.post_steps[step]:
                if not self.is_skipped(design, f'{step}.{post_step}'):
                    console.rule(f'[bold white]{design}.{step}.{post_step}[/bold white]')
                    run_stdout, run_stderr, stdout_err, stderr_err, status = self.steps.post_steps[step][post_step]["run"](self, path)
                    logfile = f'{path}/{step}.{post_step}/{step}.{post_step}.log'
                    self.logger.info(f'{step}.{post_step}, finished, output written to {logfile}')
                    with open(logfile, 'w', encoding='utf-8') as f :
                        f.write(run_stdout)
                        f.write(run_stderr)

                    if stdout_err or stderr_err or status == "fail":
                        if self.is_failure_allowed(design, f"{step}.{post_step}") is False:
                            err = True
                            errorcode = ERROR_IN_TOOL
                        self.results[design][f"{step}.{post_step}"]['status'] = 'fail'
                    elif status == "goal_not_met":
                        if self.is_failure_allowed(design, f"{step}.{post_step}") is False:
                            err = True
                            errorcode = GOAL_NOT_MET
                        self.results[design][f"{step}.{post_step}"]['status'] = 'fail'
                    else:
                        self.results[design][f"{step}.{post_step}"]['status'] = 'pass'

                # Check for keyboard interrupt after each post step
                if self.ctrl_c_pressed is True:
                    self.exit_if_required(KEYBOARD_INTERRUPT)

        return err, errorcode

    # ******************************************************************* #
    # ******************************************************************* #
    # From now on, these are (or should be!) the functions that are
    # toolchain-dependent (meaning that they have tool-specific code)
    # ******************************************************************* #
    # ******************************************************************* #
