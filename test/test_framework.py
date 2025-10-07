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

def test_set_toolchain() :
    fvm = fvmframework()
    fvm.set_toolchain("sby")

def test_set_toolchain_doesnt_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toolchain("no_toolchain")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

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

def test_clear_vhdl_sources() :
    fvm = fvmframework()
    assert len(fvm.vhdl_sources) == 0
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")
    assert len(fvm.vhdl_sources) == 1
    fvm.clear_vhdl_sources()
    assert len(fvm.vhdl_sources) == 0

def test_add_single_psl_source_exists():
    fvm = fvmframework()
    Path('test/test.psl').touch()
    fvm.add_psl_source("test/test.psl")

def test_add_single_psl_source_doesnt_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_source("thisfiledoesntexist.psl")
    assert pytest_wrapped_e.type == SystemExit

def test_clear_psl_sources() :
    fvm = fvmframework()
    assert len(fvm.psl_sources) == 0
    Path('test/test.psl').touch()
    fvm.add_psl_source("test/test.psl")
    assert len(fvm.psl_sources) == 1
    fvm.clear_psl_sources()
    assert len(fvm.psl_sources) == 0

def test_add_single_drom_source_exists():
    fvm = fvmframework()
    Path('test/test.json').touch()
    fvm.add_drom_source("test/test.json")

def test_add_single_drom_source_doesnt_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_drom_source("thisfiledoesntexist.json")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_clear_drom_sources() :
    fvm = fvmframework()
    assert len(fvm.drom_sources) == 0
    Path('test/test.json').touch()
    fvm.add_drom_source("test/test.json")
    assert len(fvm.drom_sources) == 1
    fvm.clear_drom_sources()
    assert len(fvm.drom_sources) == 0

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
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

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
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_multiple_drom_sources_exist() :
    fvm = fvmframework()
    Path('test/test.json').touch()
    Path('test/test2.json').touch()
    Path('test/test3.json').touch()
    fvm.add_drom_sources("test/*.json")

def test_add_multiple_drom_sources_dont_exist() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_drom_sources("test/thesefilesdontexist*.json")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_list_added_sources() :
    fvm = fvmframework()
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")
    fvm.list_vhdl_sources()
    fvm.list_psl_sources()
    fvm.list_sources()

def test_check_if_tools_exist() :
    fvm = fvmframework()
    exists = fvm.check_tool("vsim")
    assert exists == True
    exists = fvm.check_tool("qverify")
    assert exists == True
    exists = fvm.check_tool("notfoundtool")
    assert exists == False

def test_check_if_tools_exist() :
    fvm = fvmframework()
    exists = fvm.check_tool("vsim")
    assert exists == True
    exists = fvm.check_tool("qverify")
    assert exists == True
    exists = fvm.check_tool("notfoundtool")
    assert exists == False

def test_set_toplevel() :
    fvm = fvmframework()
    fvm.set_toplevel("test")

def test_set_multiple_toplevels() :
    fvm = fvmframework()
    fvm.set_toplevel(["test", "test2", "test3"])

def test_set_toplevels_duplicated() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "test3", "test2", "test"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]
 
def test_set_toplevels_reserved() :
    fvm = fvmframework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "fvm_dashboard"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_toplevels_if_a_design_exists() :
    fvm = fvmframework()
    fvm.design = "test3"
    fvm.set_toplevel(["test", "test2", "test3"])

def test_set_toplevels_if_a_different_design_exists() :
    fvm = fvmframework()
    fvm.design = "test4"
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "test3"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

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
