# Third party imports
import pytest
from pathlib import Path

# Our own imports
from fvm import fvmframework

# Error codes
BAD_VALUE = {"msg": "FVM exit condition: Bad value",
             "value" : 3}
ERROR_IN_LOG = {"msg": "FVM exit condition: Error detected during tool execution",
                 "value": 4}
GOAL_NOT_MET = {"msg": "FVM exit condition: User goal not met",
                "value": 5}
CHECK_FAILED = {"msg": "FVM exit condition: check_for_errors failed",
                "value": 6}
KEYBOARD_INTERRUPT = {"msg": "FVM exit condition: Keyboard interrupt",
                "value": 7}

# Common pre-test actions for all tests
#fvm = fvmframework(loglevel="TRACE")
#fvm.set_loglevel("TRACE")

# TODO improve tests, check output values, and parameterize

def test_add_single_vhdl_source_exists():
    fvm = fvmframework()
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")

def test_add_single_vhdl_source_doesnt_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_vhdl_source("thisfiledoesntexist.vhd")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_psl_source_exists():
    fvm = fvmframework()
    Path('test/test.psl').touch()
    fvm.add_psl_source("test/test.psl")

def test_add_single_psl_source_doesnt_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_source("thisfiledoesntexist.psl")
    assert pytest_wrapped_e.type == SystemExit

def test_add_multiple_vhdl_sources_exist() :
    fvm = fvmframework()
    Path('test/test.vhd').touch()
    Path('test/test2.vhd').touch()
    Path('test/test3.vhd').touch()
    fvm.add_vhdl_sources("test/*.vhd")

def test_add_multiple_vhdl_sources_dont_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_vhdl_sources("test/thesefilesdontexist*.vhd")
    assert pytest_wrapped_e.type == SystemExit

def test_add_multiple_psl_sources_exist() :
    fvm = fvmframework()
    Path('test/test.psl').touch()
    Path('test/test2.psl').touch()
    Path('test/test3.psl').touch()
    fvm.add_psl_sources("test/*.psl")

def test_add_multiple_psl_sources_dont_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_sources("test/thesefilesdontexist*.psl")
    assert pytest_wrapped_e.type == SystemExit

def test_list_added_sources() :
    fvm = fvmframework()
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")
    fvm.list_vhdl_sources()
    fvm.list_psl_sources()
    fvm.list_sources()

# TODO : make this throw errors if fail
def check_if_tools_exist() :
    fvm = fvmframework()
    fvm.add_vhdl_source("test.vhd")
    fvm.check_tool("vsim")
    fvm.check_tool("qverify")
    fvm.check_tool("notfoundtool")

#def test_check_library_exists_false() :
#    fvm = fvmframework()
#    exists = fvm.check_library_exists("librarythatdoesntexist")
#    assert exists == False

#def test_check_library_exists_true() :
#    fvm = fvmframework()
#    os.makedirs('test/testlib', exist_ok=True)
#    Path('test/testlib/_info').touch()
#    exists = fvm.check_library_exists("test/testlib")
#    assert exists == True

#def test_cmd_create_library() :
#    fvm = fvmframework()
#    print(f'Generating command to create library work')
#    cmd = fvm.cmd_create_library("work")
#    print(f'{cmd=}')

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

# Test that the logger generates the correct return values (check_errors() must
# return True if it has seen error and/or critical messages)
@pytest.mark.parametrize("severity,expected", messages_and_status)
def test_logger(severity, expected) :
    fvm = fvmframework()
    fvm.cont = True
    fvm.log(severity, f'Log message with {severity=}')
    retval = fvm.check_errors()
    print(f'{retval=}')
    assert retval == expected

def test_logger_twice() :
    fvm = fvmframework()
    fvm.cont = True

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
