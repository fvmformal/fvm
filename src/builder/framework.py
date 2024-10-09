# Python standard library imports
import sys
import os
import re
import glob
import shutil
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
    'rulecheck',
    'reachability',
    'resets',
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
        self.toplevel = list()
        self.current_toplevel = ''
        self.vhdl_sources = list()
        self.psl_sources = list()
        self.skip_list = list()
        self.toolchain = "questa"
        self.vhdlstd = "2008"

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

    def add_psl_source(self, src):
        """Add a single PSL source"""
        logger.info(f'Adding PSL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'VHDL source not found: {src}')
            self.exit_if_required(BAD_VALUE)
        extension = pathlib.Path(src).suffix
        if extension not in ['.psl', '.PSL'] :
            logger.warning(f'PSL source {src=} does not have a typical PSL extension extension, instead it has {extension=}')
        self.psl_sources.append(src)
        logger.debug(f'{self.psl_sources=}')

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

    def setup(self, design):

        # Create the output directories, but do not throw an error if it already
        # exists
        os.makedirs(self.outdir, exist_ok=True)
        self.current_toplevel = design
        path = self.outdir+'/'+self.current_toplevel
        os.makedirs(path, exist_ok=True)

        if self.toolchain == "questa":
            # Create .f files
            self.create_f_file(f'{path}/design.f', self.vhdl_sources)
            self.create_f_file(f'{path}/properties.f', self.psl_sources)
            self.genlintscript("lint.do", path)
            self.genrulecheckscript("rulecheck.do", path)
            self.genreachabilityscript("reachability.do", path)
            self.genresetscript("resets.do", path)
            #self.genclockscript("clocks.do", path)
            self.genprovescript("prove.do", path)

    def gencompilescript(self, filename, path):
        # TODO : we must also compile the Verilog sources, if they exist
        # TODO : we must check for the case of only-verilog designs (no VHDL files)
        # TODO : we must check for the case of only-VHDL designs (no verilog files)
        """ This is used as header for the other scripts, since we need to have
        a compiled netlist in order to do anything"""
        with open(path+'/'+filename, "w") as f:
            print('onerror exit', file=f)
            print('if {[file exists work]} {',file=f)
            print('    vdel -all', file=f)
            print('}', file=f)
            print('vlib work', file=f)
            print('vmap work work', file=f)
            print(f'vcom -{self.vhdlstd} -autoorder -f {path}/design.f', file=f)
            print('', file=f)

    def genresetscript(self, filename, path):
        # We first write the header to compile the netlist  and then append
        # (mode "a") the tool-specific instructions
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            # TODO : let the user specify clock names, polarities, sync/async,
            # clock domains and reset domains
            #print('netlist reset rst -active_high -async', file=f)
            #print('netlist port domain rst -clock clk', file=f)
            #print('netlist port domain data -clock clk', file=f)
            #print('netlist port domain empty -clock clk', file=f)
            #print('netlist port resetdomain data -reset rst', file=f)
            #print('netlist port resetdomain empty -reset rst', file=f)
            #print('netlist clock clk', file=f)

            print(f'rdc run -d {self.current_toplevel}', file=f)
            print('rdc generate report -resetcheck reset_report.rpt;', file=f)
            print('rdc generate tree -reset reset_tree.rpt;', file=f)
            print('exit', file=f)

    # TODO : we will need arguments for the clocks, timeout, we probably need
    # to detect compile order if vcom doesn't detect it, set the other options
    # such as timeout... and also throw some errors if any option is not
    # specified. This is not trivial. Also, in the future we may want to
    # specify verilog files with vlog, etc...
    # TODO : can we also compile the PSL files using a .f file?
    def genprovescript(self, filename, path):
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print('', file=f)
            print('## Add clocks', file=f)
            #print('log_info "***** Adding clocks..."', file=f)
            print('netlist clock clk -period 10', file=f)
            print('', file=f)
            print('## Run PropCheck', file=f)
            #print('log_info "***** Running formal compile (compiling formal model)..."', file=f)

            print('formal compile ', end='', file=f)
            for i in self.psl_sources :
                print(f'-pslfile {i} ', end='', file=f)
            print('-include_code_cov ', end='', file=f)
            print(f'-d {self.current_toplevel}', file=f)

            #print('log_info "***** Running formal verify (model checking)..."', file=f)
            print('formal verify -auto_constraint_off -cov_mode -timeout 10m', file=f)
            print('', file=f)
            print('## Compute Formal Coverage', file=f)
            #print('log_info "***** Running formal verify to get coverage..."', file=f)
            # TODO : Coverage collection temporarily disabled since we get some
            # errors in example 05-uart_tx which we need to solve (we must add
            # some kind of exclusion for reset state transitions). The next
            # line is the one that raises the errors of type:
            # "Uncoverable FSM: FSM 'estado', Transition sampledata -> reposo"
            print('formal verify -auto_constraint_off -cov_mode reachability -timeout 10m', file=f)
            #print('log_info "***** Running formal generate coverage..."', file=f)
            print('formal generate coverage -cov_mode o', file=f)
            print('formal generate coverage -cov_mode s', file=f)
            print('formal generate coverage -cov_mode r', file=f)
            print('formal generate coverage -cov_mode b', file=f)
            print('formal generate report', file=f)
            print('', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too
    # i.e., lint methodology, goal, etc
    def genlintscript(self, filename, path):
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print('lint methodology ip -goal start', file=f)
            print(f'lint run -d {self.current_toplevel}', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too
    def genrulecheckscript(self, filename, path):
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'autocheck compile -d {self.current_toplevel}', file=f)
            print(f'autocheck verify', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too,
    # such as allowing the user to specify the covercheck directives
    # TODO : if a .ucdb file is specified as argument, run the post-simulation
    # analysis instead of the pre-simulation analysis (see
    # https://git.woden.us.es/eda/fvm/-/issues/37#note_4252)
    def genreachabilityscript(self, filename, path):
        self.gencompilescript(filename, path)
        with open(path+'/'+filename, "a") as f:
            print(f'covercheck compile -d {self.current_toplevel}', file=f)
            # if .ucdb file is specified:
            #    print('covercheck load ucdb {ucdb_file}', file=f)
            #    print(f'covercheck verify -covered_items', file=f)
            print(f'covercheck verify', file=f)
            print('exit', file=f)

    def run(self):
        print(f'{self.toplevel=}')
        for design in self.toplevel:
            print(f'Running {design=}')
            self.run_design(design)

        self.pretty_summary()
        err = self.check_errors()
        if err :
          self.exit_if_required(CHECK_FAILED)

    def run_design(self, design):
        """Run all available/selected methodology steps"""
        # Create all necessary scripts
        self.setup(design)

        # Run all available/selected steps/tools
        # Call the run_step() function for each available step
        # If a 'step' argument is specified, just run that specific step
        if self.step is None:
            for step in FVM_STEPS:
                if self.is_skipped(design, step):
                    logger.info(f'{step=} of {design=} skipped by skip() function, will not run')
                    self.results[design][step]['status'] = 'skip'
                elif step in toolchains.TOOLS[self.toolchain]:
                    self.run_step(design, step)
                else:
                    logger.info(f'{step=} not available in {self.toolchain=}, skipping')
                    self.results[design][step]['status'] = 'skip'
        else:
            self.run_step(design, self.step)

    def is_skipped(self, design, step):
        """Returns True if design.step must not be run, otherwise returns False"""
        for skip_str in self.skip_list:
            if fnmatch.fnmatch(f'{design}.{step}', skip_str):
                return True
        return False


    # TODO : we have some duplicated code in the way we run commands, becase
    # the code sort of repeats for the GUI invocations. We must see how we can
    # deduplicate this so this function does not get unwieldy
    def run_step(self, design, step):
        """Run a specific step of the methodology"""
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
                    stdout_err = self.logcheck(cmd_stdout, step, tool)
                    stderr_err = self.logcheck(cmd_stderr, step, tool)
                    logfile = f'{path}/{step}.log'
                    logger.info(f'{step=}, {tool=}, finished, output written to {logfile}')
                    with open(logfile, 'w') as f :
                        f.write(cmd_stdout)
                        f.write(cmd_stderr)
                    # TODO : we disabled this error, we should propagate the
                    # error outside
                    #if stdout_err or stderr_err:
                    #    self.exit_if_required(ERROR_IN_LOG)
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

    def run_cmd(self, cmd, design, step, tool, verbose = True):
        self.set_logformat(getlogformattool(design, step, tool))

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

    def logcheck(self, result, step, tool):
        err_in_log = False
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
        return err_in_log

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

    def pretty_summary(self):
        """Prints the final summary"""
        # TODO : use rich or a similar python package to format a table
        # TODO : print the status for each design.step
        # TODO : color the status
        # TODO : print also number of warnings and errors, and all relevant
        # information from propchech (number of
        # assume/assert/fired/proven/cover/covered/uncoverable/etc. For this,
        # we may need to post-process the prove step log
        # TODO : print elapsed time
        print("==== Summary ====================================")
        for design in self.toplevel:
            for step in FVM_STEPS:
                # Only print pass/fail/skip, the rest of steps where not
                # selected by the user so there is no need to be redundant
                if 'status' in self.results[design][step]:
                    status = self.results[design][step]['status']
                    text = Text()
                    if status == 'pass':
                        style = 'bold green'
                    elif status == 'fail':
                        style = 'bold red'
                    elif status == 'skip':
                        style = 'bold yellow'
                    text.append(status, style=style)
                    text.append(f' {design}.{step}')
                    #text.append(f' result={self.results[design][step]}', style='white')
                    console.print(text)
                    #print(f'{status} {design}.{step}, result={self.results[design][step]}')
        print("=================================================")

    def exit_if_required(self, errorcode):
        """Exit if the continue flag is not set"""
        if self.cont:
            pass
        else:
            sys.exit(errorcode)
