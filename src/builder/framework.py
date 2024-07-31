# Python standard library imports
import sys
import os
import re
import glob
import shutil
import subprocess
import pathlib

# Third party imports
import argparse
from loguru import logger

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
LOGFORMAT_TOOL = '<cyan>FVM</cyan> | <green>Tool</green> | <level>{level: <8}</level> | <level>{message}</level>'

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
        parser.add_argument('-s', '--step',
                help='If set, run the specified step. It unset, run all steps. (default: %(default)s)')
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
        self.toplevel = ''
        self.vhdl_sources = list()
        self.psl_sources = list()
        self.toolchain = "questa"

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
        self.toplevel = toplevel

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

    def setup(self):
        # Create the output directory, but do not throw an error if it already
        # exists
        os.makedirs(self.outdir, exist_ok=True)

        if self.toolchain == "questa":
            # Create .f files
            self.create_f_file(self.outdir+'/'+"design.f", self.vhdl_sources)
            self.create_f_file(self.outdir+'/'+"properties.f", self.psl_sources)
            self.genprovescript(self.outdir+'/'+"prove.do")
            self.genlintscript(self.outdir+'/'+"lint.do")

    # TODO : we will need arguments for the clocks, timeout, we probably need
    # to detect compile order if vcom doesn't detect it, set the other options
    # such as timeout... and also throw some errors if any option is not
    # specified. This is not trivial. Also, in the future we may want to
    # specify verilog files with vlog, etc...
    # TODO : can we also compile the PSL files using a .f file?
    def genprovescript(self, filename):
        with open(filename, "w") as f:
            print('onerror exit', file=f)
            print('', file=f)
            #print('source ../scripts/color.tcl')
            print('', file=f)
            print('## Compile netlist', file=f)
            #print('log_info "***** Compiling netlist..."')
            print(f'vcom -autoorder -f {self.outdir}/design.f', file=f)

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
            print(f'-d {self.toplevel}', file=f)

            #print('log_info "***** Running formal verify (model checking)..."', file=f)
            print('formal verify -auto_constraint_off -cov_mode -timeout 10m', file=f)
            print('', file=f)
            print('# Compute Formal Coverage', file=f)
            #print('log_info "***** Running formal verify to get coverage..."', file=f)
            print('formal verify -auto_constraint_off -cov_mode reachability -timeout 10m', file=f)
            #print('log_info "***** Running formal generate coverage..."', file=f)
            print('formal generate coverage -cov_mode s', file=f)
            print('formal generate coverage -cov_mode b', file=f)
            print('formal generate coverage -cov_mode r', file=f)
            print('formal generate coverage -cov_mode o', file=f)
            print('', file=f)
            print('exit', file=f)

    # TODO : set sensible defaults here and allow for user optionality too
    # i.e., lint methodology, goal, etc
    def genlintscript(self, filename):
        with open(filename, "w") as f:
            print('onerror exit', file=f)
            print('lint methodology ip -goal start', file=f)
            print('vlib work', file=f)
            print('vmap work work', file=f)
            print(f'vcom -autoorder -f {self.outdir}/design.f', file=f)
            print(f'lint run -d {self.toplevel}', file=f)
            print('exit', file=f)

    def run(self):
        # Run all available/selected steps/tools
        # Call the run_step() function for each available step
        # If a 'step' argument is specified, just run that specific step
        if self.step is None:
            self.run_step("lint")
            self.run_step("prove")
        else:
            self.run_step(self.step)

    # TODO : we have some duplicated code in the way we run commands, becase
    # the code sort of repeats for the GUI invocations. We must see how we can
    # deduplicate this so this function does not get unwieldy
    def run_step(self, step):
        """Run a specific step of the methodology"""
        open_gui = False
        # If called with a specific step, run that specific step
        if step in toolchains.TOOLS[self.toolchain] :
            tool = toolchains.TOOLS[self.toolchain][step]
            logger.info(f'{step=}, running {tool=}')
            logger.debug(f'Running {tool=}')
            if self.toolchain == "questa":
                cmd = [tool, '-c', '-od', self.outdir, '-do', self.outdir+'/'+step+'.do']
                logger.trace(f'command: {" ".join(cmd)=}')
                if self.list == True :
                    logger.info(f'Available step: {step}. Tool: {tool}, command = {" ".join(cmd)}')
                elif self.guinorun == True :
                    logger.info(f'{self.guinorun=}, will not run {step=} with {tool=}')
                else :
                    cmd_stdout, cmd_stderr = self.run_cmd(cmd, self.verbose)
                    stdout_err = self.logcheck(cmd_stdout, step, tool)
                    stderr_err = self.logcheck(cmd_stderr, step, tool)
                    logfile = f'{self.outdir}/{step}.log'
                    logger.info(f'{step=}, {tool=} output written to {logfile}')
                    with open(logfile, 'w') as f :
                        f.write(cmd_stdout)
                        f.write(cmd_stderr)
                    if stdout_err or stderr_err:
                        self.exit_if_required(ERROR_IN_LOG)
                    if self.gui :
                        open_gui = True
                if self.guinorun and self.list == False :
                    open_gui = True
                if open_gui:
                    logger.info(f'{step=}, {tool=}, opening results with GUI')
                    if step == "lint":
                        cmd = [tool, f'{self.outdir}'+'/'+'lint.db']
                        self.run_cmd(cmd, self.verbose)
                        # TODO : maybe check for errors also in the GUI?
                        # TODO : maybe run the GUI processes without blocking
                        # the rest of the steps? For that we would probably
                        # need to pass nother option to run_cmd
                    elif step == "prove":
                        cmd = [tool, f'{self.outdir}'+'/'+'propcheck.db']
                        self.run_cmd(cmd, self.verbose)
                        # TODO : maybe check for errors also in the GUI?
                        # TODO : maybe run the GUI processes without blocking
                        # the rest of the steps? For that we would probably
                        # need to pass nother option to run_cmd
        else :
            logger.error(f'No tool available for {step=} in {self.toolchain=}')
            self.exit_if_required(BAD_VALUE)

    def run_cmd(self, cmd, verbose = True):
        self.set_logformat(LOGFORMAT_TOOL)

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

        # If verbose, read and print stdout and stderr in real-time
        with process.stdout as stdout, process.stderr as stderr:
            for line in iter(stdout.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn = self.linecheck(line)
                    if err:
                        logger.error(line.rstrip())
                    elif warn:
                        logger.warning(line.rstrip())
                    else:
                        logger.trace(line.rstrip())
                stdout_lines.append(line)  # Save to list

            for line in iter(stderr.readline, ''):
                # If verbose, print to console
                if verbose:
                    err, warn = self.linecheck(line)
                    if err:
                        logger.error(line.rstrip())
                    elif warn:
                        logger.warning(line.rstrip())
                    else:
                        logger.trace(line.rstrip())
                stderr_lines.append(line)  # Save to list

        # Wait for the process to complete and get the return code
        retval = process.wait()

        # Join captured output
        captured_stdout = ''.join(stdout_lines)
        captured_stderr = ''.join(stderr_lines)

        # Raise an exception if the return code is non-zero
        if retval != 0:
            raise subprocess.CalledProcessError(return_code, cmd, output=captured_stdout, stderr=captured_stderr)

        self.set_logformat(LOGFORMAT)

        return captured_stdout, captured_stderr

    def logcheck(self, result, step, tool):
        err_in_log = False
        for line in result.splitlines() :
            err, warn = self.linecheck(line)
            if err :
                logger.error(f'ERROR detected in {step=}, {tool=}, {line=}')
                err_in_log = True
            elif warn :
                logger.warning(f'WARNING detected in {step=}, {tool=}, {line=}')
        return err_in_log

    def linecheck(self, line):
        """Check for errors and warnings in log lines. Use casefold() for
        robust case-insensitive comparison"""
        err = False
        warn = False
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
        return err, warn

    def exit_if_required(self, errorcode):
        """Exit if the continue flag is not set"""
        if self.cont:
            pass
        else:
            sys.exit(errorcode)
