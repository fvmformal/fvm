# Python standard library imports
import sys
import os
import glob
import shutil

# Third party imports
from loguru import logger

# Our own imports
from src.builder import toolchains
from src.builder import logcounter

LOGFORMAT = '<cyan>FVM</cyan> | <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
LOGFORMAT_SUMMARY = '<cyan>FVM</cyan> | <green>Summary</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'

class fvmframework:

    def __init__(self, loglevel="INFO", outdir="fvm_out"):
        """Class constructor"""

        # Make loglevel an instance variable
        self.loglevel = loglevel

        # Create logger counter
        self.log_counter = logcounter.logcounter()

        # Create logger object
        logger.info(f'Creating {self}')

        # Clean logger format and handlers
        logger.remove()

        # Add log_counter as custom handler so log messages are counted
        # include all message types (from level 0 onwards) so they get recorded
        # even if they are not printed
        logger.add(self.log_counter, level=0)

        # Get log messages also in stderr. Only print format
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

        # Rest of instance variables
        self.vhdl_sources = list()
        self.psl_sources = list()
        self.toolchain = "questa"
        self.outdir = outdir

    def add_vhdl_source(self, src):
        """Add a single VHDL source"""
        logger.info(f'Adding VHDL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'VHDL source not found: {src}')
        self.vhdl_sources.append(src)
        logger.debug(f'{self.vhdl_sources=}')

    def add_psl_source(self, src):
        """Add a single PSL source"""
        logger.info(f'Adding PSL source: {src}')
        if not os.path.exists(src) :
            logger.error(f'VHDL source not found: {src}')
        self.psl_sources.append(src)
        logger.debug(f'{self.psl_sources=}')

    def add_vhdl_sources(self, globstr):
        """Add multiple VHDL sources by globbing a pattern"""
        sources = glob.glob(globstr)
        if len(sources) == 0 :
            logger.error(f'No files found for pattern {globstr}')
        for source in sources:
            self.add_vhdl_source(source)

    def add_psl_sources(self, globstr):
        """Add multiple PSL sources by globbing a pattern"""
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

    def set_loglevel(self, loglevel):
        """Sets the logging level for the build and test framework.

        @param loglevel: must be one of loguru's allowed log levels: TRACE,
        DEBUG, INFO, SUCCESS, WARNING, ERROR, or CRITICAL"""
        # TODO : maybe we will just remove some of these loglevels as valid
        # options if we end up using those log levels to indicate normal
        # operation of our framework
        logger.remove()
        self.loglevel = loglevel
        logger.add(sys.stderr, level=self.loglevel, format=LOGFORMAT)

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
        print(f'{msg_counts=}')

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

        return ret

    # From now on, these are the functions that are toolchain-dependent
    # (meaning that they have tool-specific code)

    def set_toolchain(self, toolchain) :
        if toolchain not in toolchains.TOOLS :
            logger.error(f'{toolchain=} not supported')
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

    def cmd_create_library(self, lib) :
        if self.toolchain == "questa" :
            cmd = toolchains.TOOLS[self.toolchain]["createemptylib"] + ' ' + lib
        return cmd


