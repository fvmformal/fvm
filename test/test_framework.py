# Third party imports
import pytest

# Our own imports
from src.builder.framework import fvmframework

# Common pre-test actions for all tests
#fvm = fvmframework(loglevel="TRACE")
#fvm.set_loglevel("TRACE")

# TODO improve tests, check output values, and parameterize

def test_add_single_source() :
    # Add single source
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.add_psl_source("test.psl")
    fvm.add_vhdl_source("test2.vhd")

# Add multiple sources
def test_add_multiple_sources() :
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.add_vhdl_sources("*.vhdl")
    fvm.add_psl_sources("*.psl")
    fvm.add_vhdl_sources("otherfiles*.vhd")
    fvm.add_psl_sources("otherfiles*.vhd")

def test_list_added_sources() :
    # List added sources
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.list_vhdl_sources()
    fvm.list_psl_sources()
    fvm.list_sources()

def check_if_tools_exist() :
    # Check if tools exist
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.check_tool("vsim")
    fvm.check_tool("qverify")
    fvm.check_tool("notfoundtool")

def test_check_library_exists() :
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.check_library_exists("work")

def test_cmd_create_library() :
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    print(f'Generating command to create library work')
    cmd = fvm.cmd_create_library("work")
    print(f'{cmd=}')

# Message levels that should return an error appear as "True" in the following
# table
messages_and_status = [
    ("trace", False),
    ("TRACE", False),
    ("debug", False),
    ("DEBUG", False),
    ("info", False),
    ("INFO", False),
    ("success", False),
    ("SUCCESS", False),
    ("warning", False),
    ("WARNING", False),
    ("error", True),
    ("ERROR", True),
    ("critical", True),
    ("CRITICAL", True)
    ]

@pytest.mark.parametrize("severity,expected", messages_and_status)
def test_logger(severity, expected) :
    fvm = fvmframework(loglevel="TRACE")
    fvm.log(severity, f'Log message with {severity=}')
    retval = fvm.check_errors()
    print(f'{retval=}')
    assert retval == expected

def test_logger_twice() :
    fvm = fvmframework(loglevel="TRACE")

    fvm.log("success", "Success message")

    # First time we should see an error
    fvm.log("error", "Error message")
    retval = fvm.check_errors()
    print(f'{retval=}')
    assert retval == True

    # Second time we should still see the error from before. If we don't, it
    # means we inadvertently deleted the message counts
    fvm.log("warning", "Warning message")
    retval = fvm.check_errors()
    print(f'{retval=}')
    assert retval == True


