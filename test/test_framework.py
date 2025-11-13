"""Unit tests for FvmFramework class"""
from pathlib import Path
import shutil
import subprocess

# Third party imports
import pytest

# Our own imports
from fvm import FvmFramework

# Error codes
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

# Common pre-test actions for all tests
#fvm = FvmFramework(loglevel="TRACE")
#fvm.set_loglevel("TRACE")

def test_set_toolchain() :
    """Test setting a toolchain that exists"""
    fvm = FvmFramework()
    fvm.set_toolchain("sby")

def test_set_toolchain_doesnt_exist() :
    """Test setting a toolchain that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toolchain("no_toolchain")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_vhdl_source_exists():
    """Test adding a single VHDL source file that exists"""
    fvm = FvmFramework()
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")

def test_add_single_vhdl_source_doesnt_exist() :
    """Test adding a single VHDL source file that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_vhdl_source("thisfiledoesntexist.vhd")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_verilog_source_exists():
    """Test adding a single Verilog source file that exists"""
    fvm = FvmFramework()
    Path('test/test.v').touch()
    fvm.add_verilog_source("test/test.v")
    # Add verilog source without typical verilog extension
    fvm.add_verilog_source("test/test.vhd")

def test_add_single_verilog_source_doesnt_exist() :
    """Test adding a single Verilog source file that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_verilog_source("thisfiledoesntexist.v")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_systemverilog_source_exists():
    """Test adding a single SystemVerilog source file that exists"""
    fvm = FvmFramework()
    Path('test/test.sv').touch()
    fvm.add_systemverilog_source("test/test.sv")
    # Add systemverilog source without typical systemverilog extension
    fvm.add_systemverilog_source("test/test.vhd")

def test_add_single_systemverilog_source_doesnt_exist() :
    """Test adding a single SystemVerilog source file that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_systemverilog_source("thisfiledoesntexist.sv")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_clear_vhdl_sources() :
    """Test clearing the list of VHDL source files"""
    fvm = FvmFramework()
    assert len(fvm.vhdl_sources) == 0
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")
    assert len(fvm.vhdl_sources) == 1
    fvm.clear_vhdl_sources()
    assert len(fvm.vhdl_sources) == 0

def test_clear_verilog_sources() :
    """Test clearing the list of Verilog source files"""
    fvm = FvmFramework()
    assert len(fvm.verilog_sources) == 0
    Path('test/test.v').touch()
    fvm.add_verilog_source("test/test.v")
    assert len(fvm.verilog_sources) == 1
    fvm.clear_verilog_sources()
    assert len(fvm.verilog_sources) == 0

def test_clear_systemverilog_sources() :
    """Test clearing the list of SystemVerilog source files"""
    fvm = FvmFramework()
    assert len(fvm.systemverilog_sources) == 0
    Path('test/test.sv').touch()
    fvm.add_systemverilog_source("test/test.sv")
    assert len(fvm.systemverilog_sources) == 1
    fvm.clear_systemverilog_sources()
    assert len(fvm.systemverilog_sources) == 0

def test_add_single_psl_source_exists():
    """Test adding a single PSL source file that exists"""
    fvm = FvmFramework()
    Path('test/test.psl').touch()
    fvm.add_psl_source("test/test.psl", flavor="vhdl")

def test_add_single_psl_source_doesnt_exist() :
    """Test adding a single PSL source file that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_source("thisfiledoesntexist.psl", flavor="vhdl")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_psl_source_invalid_flavor() :
    """Test adding a single PSL source file with an invalid flavor"""
    fvm = FvmFramework()
    Path('test/test.psl').touch()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_source("test/test.psl", flavor="invalid")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_clear_psl_sources() :
    """Test clearing the list of PSL source files"""
    fvm = FvmFramework()
    assert len(fvm.psl_sources) == 0
    Path('test/test.psl').touch()
    fvm.add_psl_source("test/test.psl", flavor="vhdl")
    assert len(fvm.psl_sources) == 1
    fvm.clear_psl_sources()
    assert len(fvm.psl_sources) == 0

def test_add_single_drom_source_exists():
    """Test adding a single Wavedrom source file that exists"""
    fvm = FvmFramework()
    Path('test/test.json').touch()
    fvm.add_drom_source("test/test.json", flavor="vhdl")

def test_add_single_drom_source_doesnt_exist() :
    """Test adding a single Wavedrom source file that doesn't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_drom_source("thisfiledoesntexist.json", "vhdl")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_single_drom_source_verilog() :
    """Test adding a single Wavedrom with verilog flavor (not supported yet)"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_drom_source("test/test.json", "verilog")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_clear_drom_sources() :
    """Test clearing the list of Wavedrom source files"""
    fvm = FvmFramework()
    assert len(fvm.drom_sources) == 0
    Path('test/test.json').touch()
    fvm.add_drom_source("test/test.json", "vhdl")
    assert len(fvm.drom_sources) == 1
    fvm.clear_drom_sources()
    assert len(fvm.drom_sources) == 0

def test_add_multiple_vhdl_sources_exist() :
    """Test adding multiple VHDL source files that exist"""
    fvm = FvmFramework()
    Path('test/test.vhd').touch()
    Path('test/test2.vhd').touch()
    Path('test/test3.vhd').touch()
    fvm.add_vhdl_sources("test/*.vhd")

def test_add_multiple_vhdl_sources_dont_exist() :
    """Test adding multiple VHDL source files that don't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_vhdl_sources("test/thesefilesdontexist*.vhd")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_multiple_verilog_sources_exist() :
    """Test adding multiple Verilog source files that exist"""
    fvm = FvmFramework()
    Path('test/test.v').touch()
    Path('test/test2.v').touch()
    Path('test/test3.v').touch()
    fvm.add_verilog_sources("test/*.v")

def test_add_multiple_verilog_sources_dont_exist() :
    """Test adding multiple Verilog source files that don't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_verilog_sources("test/thesefilesdontexist*.v")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_multiple_systemverilog_sources_exist() :
    """Test adding multiple SystemVerilog source files that exist"""
    fvm = FvmFramework()
    Path('test/test.sv').touch()
    Path('test/test2.sv').touch()
    Path('test/test3.sv').touch()
    fvm.add_systemverilog_sources("test/*.sv")

def test_add_multiple_systemverilog_sources_dont_exist() :
    """Test adding multiple SystemVerilog source files that don't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_systemverilog_sources("test/thesefilesdontexist*.sv")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_multiple_psl_sources_exist() :
    """Test adding multiple PSL source files that exist"""
    fvm = FvmFramework()
    Path('test/test.psl').touch()
    Path('test/test2.psl').touch()
    Path('test/test3.psl').touch()
    fvm.add_psl_sources("test/*.psl", flavor="vhdl")

def test_add_multiple_psl_sources_dont_exist() :
    """Test adding multiple PSL source files that don't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_psl_sources("test/thesefilesdontexist*.psl", flavor="vhdl")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_multiple_drom_sources_exist() :
    """Test adding multiple Wavedrom source files that exist"""
    fvm = FvmFramework()
    Path('test/test.json').touch()
    Path('test/test2.json').touch()
    Path('test/test3.json').touch()
    fvm.add_drom_sources("test/*.json", flavor="vhdl")

def test_add_multiple_drom_sources_dont_exist() :
    """Test adding multiple Wavedrom source files that don't exist"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_drom_sources("test/thesefilesdontexist*.json", flavor="vhdl")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_list_added_sources() :
    """Test listing added source files"""
    fvm = FvmFramework()
    Path('test/test.vhd').touch()
    fvm.add_vhdl_source("test/test.vhd")
    fvm.list_vhdl_sources()
    fvm.list_psl_sources()
    fvm.list_sources()

def test_check_if_tools_exist() :
    """Test checking if tools exist in PATH"""
    fvm = FvmFramework()
    exists = fvm.check_tool("ls")
    assert exists == True
    exists = fvm.check_tool("notfoundtool")
    assert exists == False

def test_qverify_not_in_path(monkeypatch):
    """Test simulating that 'qverify' is not in PATH"""

    # Save the original function before patching
    real_which = shutil.which

    # Simulate that 'qverify' is not found
    monkeypatch.setattr(shutil, "which", lambda x: None if x == "qverify" else real_which(x))

    # Quick check (optional)
    assert shutil.which("qverify") is None

    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.run()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ERROR_IN_TOOL["value"]

def test_remove_csh_from_path(monkeypatch):
    """Simulate that csh is not available, regardless of PATH"""

    # Save the original function before patching
    real_which = shutil.which

    # Simulate that 'csh' is not found
    monkeypatch.setattr(shutil, "which", lambda x: None if x == "csh" else real_which(x))

    # Now any call to which("csh") returns None
    assert shutil.which("csh") is None

    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")
    fvm.step = "prove"
    fvm.skip("prove.formalcover")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.run()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ERROR_IN_TOOL["value"]

def test_remove_vcover_from_path(monkeypatch):
    """
    Simulate that vcover is not available, regardless of PATH.
    Also test that shownorun mode works.
    """

    # Save the original function before patching
    real_which = shutil.which

    # Simulate that 'vcover' is not found
    monkeypatch.setattr(shutil, "which", lambda x: None if x == "vcover" else real_which(x))

    # Now any call to which("vcover") returns None
    assert shutil.which("vcover") is None

    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")
    fvm.step = "prove"
    fvm.skip("prove.formalcover")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.run()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ERROR_IN_TOOL["value"]

def test_shownorun_fail():
    """Test --shownorun argument"""
    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")
    fvm.shownorun = True
    fvm.outdir = "doesnt_exist"

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.run()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == CHECK_FAILED["value"]

def test_showall(monkeypatch):
    """Test --showall argument"""
    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")
    fvm.showall = True

    # Fake subprocess.Popen
    class DummyProc:
        def wait(self): return 0

    def fake_popen(*a, **kw):
        print(f"Simulating Popen: {a}")
        return DummyProc()

    # Only fake subprocess in this test
    with monkeypatch.context() as m:
        m.setattr(subprocess, "Popen", fake_popen)
        fvm.run()

def test_showall_fail():
    """Test --showall argument"""
    fvm = FvmFramework()
    fvm.add_vhdl_source("examples/counter/counter.vhd")
    fvm.set_toplevel("counter")
    fvm.showall = True
    fvm.outdir = "doesnt_exist_2"

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.run()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == CHECK_FAILED["value"]

def test_set_prefix() :
    """Test setting a valid prefix"""
    fvm = FvmFramework()
    fvm.set_prefix("prefix")
    assert fvm.prefix == "prefix"

def test_set_prefix_no_str() :
    """Test setting an invalid prefix (not a string)"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_prefix(2)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]
    assert fvm.prefix != 2

def test_set_vhdl_std() :
    """Test setting a valid VHDL standard"""
    fvm = FvmFramework()
    fvm.set_vhdl_std("93")
    assert fvm.vhdlstd == "93"

def test_set_vhdl_std_invalid() :
    """Test setting an invalid VHDL standard"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_vhdl_std("invalid")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_vhdl_std_integer() :
    """Test setting an invalid VHDL standard"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_vhdl_std(93)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_get_vhdl_std() :
    """Test getting the current VHDL standard"""
    fvm = FvmFramework()
    fvm.set_vhdl_std("02")
    vhdlstd = fvm.get_vhdl_std()
    assert vhdlstd == "02"

def test_set_toplevel() :
    """Test setting a valid toplevel"""
    fvm = FvmFramework()
    fvm.set_toplevel("test")

def test_set_multiple_toplevels() :
    """Test setting multiple valid toplevels"""
    fvm = FvmFramework()
    fvm.set_toplevel(["test", "test2", "test3"])

def test_set_toplevels_duplicated() :
    """Test setting multiple toplevels with duplicates"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "test3", "test2", "test"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_toplevels_reserved() :
    """Test setting multiple toplevels with a reserved name"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "fvm_dashboard"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_toplevels_if_a_design_exists() :
    """Test setting multiple toplevels when a design is already set"""
    fvm = FvmFramework()
    fvm.design = "test3"
    fvm.set_toplevel(["test", "test2", "test3"])

def test_set_toplevels_if_a_different_design_exists() :
    """Test setting multiple toplevels when a different design is already set"""
    fvm = FvmFramework()
    fvm.design = "test4"
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_toplevel(["test", "test2", "test3"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_add_config() :
    """Test adding a configuration for a toplevel"""
    fvm = FvmFramework()
    fvm.set_toplevel(["test1", "test2", "test3"])
    fvm.add_config("test1", "config1", {"generic1": 1, "generic2": 2})

def test_add_config_before_set_toplevel() :
    """Test adding a configuration before setting toplevels"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.add_config("test", "config1", {"generic1": 1, "generic2": 2})
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_skip_step() :
    """Test skipping a step"""
    fvm = FvmFramework()
    fvm.skip("lint", "test")

def test_skip_invalid() :
    """Test skipping an invalid step"""
    fvm = FvmFramework()
    fvm.skip("Not implemented yet", "test")

def test_allow_failure_step() :
    """Test allowing failure of a step"""
    fvm = FvmFramework()
    fvm.allow_failure("lint", "test")

def test_allow_failure_invalid() :
    """Test allowing failure of an invalid step"""
    fvm = FvmFramework()
    fvm.allow_failure("Not implemented yet", "test")

def test_disable_coverage_o() :
    """Test disabling observability coverage"""
    fvm = FvmFramework()
    fvm.disable_coverage("observability", "test")

def test_disable_coverage_s() :
    """Test disabling signoff coverage"""
    fvm = FvmFramework()
    fvm.disable_coverage("signoff", "test")

def test_disable_coverage_r() :
    """Test disabling reachability coverage"""
    fvm = FvmFramework()
    fvm.disable_coverage("reachability", "test")

def test_disable_coverage_b() :
    """Test disabling bounded reachability coverage"""
    fvm = FvmFramework()
    fvm.disable_coverage("bounded_reachability", "test")

def test_disable_coverage_covtype_not_valid() :
    """Test disabling coverage with an invalid coverage type"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.disable_coverage("not valid", "test")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_timeout() :
    """Test setting a valid timeout"""
    fvm = FvmFramework()
    fvm.set_timeout("xverify", "1m")

def test_set_timeout_prove() :
    """Test setting a valid timeout for the 'prove' step"""
    fvm = FvmFramework()
    fvm.set_timeout("prove", "5m")

def test_set_timeout_invalid() :
    """Test setting a timeout with an invalid step name"""
    fvm = FvmFramework()
    fvm.set_timeout("invalid", "5m")

def test_set_coverage_goal_float() :
    """Test setting a valid coverage goal as a float"""
    fvm = FvmFramework()
    fvm.set_coverage_goal("reachability", 90.0)

def test_set_coverage_goal_int() :
    """Test setting a valid coverage goal as an integer"""
    fvm = FvmFramework()
    fvm.set_coverage_goal("reachability", 90)

def test_set_coverage_goal_wrong_type() :
    """Test setting a coverage goal with an invalid type (string)"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_coverage_goal("reachability", "90")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_coverage_goal_wrong_range() :
    """Test setting a coverage goal with an invalid range (>100)"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_coverage_goal("reachability", 150)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_coverage_goal_wrong_range_2() :
    """Test setting a coverage goal with an invalid range (<0)"""
    fvm = FvmFramework()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        fvm.set_coverage_goal("reachability", -20)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BAD_VALUE["value"]

def test_set_coverage_goal_step_invalid() :
    """Test setting a coverage goal with an invalid step name"""
    fvm = FvmFramework()
    fvm.set_coverage_goal("wrong", 10)

def test_formal_initialize_reset_active_high() :
    """Test formal_initialize_reset with active high reset"""
    fvm = FvmFramework()
    fvm.formal_initialize_reset("rst", active_high=True, cycles=3)
    fvm.setup_design("toplevel")

def test_formal_initialize_reset_active_low() :
    """Test formal_initialize_reset with active low reset"""
    fvm = FvmFramework()
    fvm.formal_initialize_reset("reset", active_high=False, cycles=1)
    fvm.setup_design("toplevel")

def test_set_pre_hook() :
    """Test setting a pre-hook"""
    fvm = FvmFramework()
    fvm.set_pre_hook("echo pre-hook", "xverify")

def test_set_pre_hook_invalid_step() :
    """Test setting a pre-hook with an invalid step name"""
    fvm = FvmFramework()
    fvm.set_pre_hook("echo pre-hook", "invalid")

def test_set_post_hook() :
    """Test setting a post-hook"""
    fvm = FvmFramework()
    fvm.set_post_hook("echo post-hook", "xverify")

def test_set_post_hook_invalid_step() :
    """Test setting a post-hook with an invalid step name"""
    fvm = FvmFramework()
    fvm.set_post_hook("echo post-hook", "invalid")

def test_set_loglevel() :
    """Test setting the log level"""
    fvm = FvmFramework()
    fvm.set_loglevel("ERROR")

def test_log() :
    """Test logging messages at different levels"""
    fvm = FvmFramework()
    fvm.log("info", "This is an info message")
    fvm.log("error", "This is an error message")

def test_add_clock_domain() :
    """Test adding a clock domain. Arguments can be contradictory, as we are just
    testing the interface here."""
    fvm = FvmFramework()
    fvm.add_clock_domain(["rst", "enable"], clock_name="clk", asynchronous=True,
                         ignore=True, posedge=True, negedge=True, module="toplevel",
                         inout_clock_in="clk_in", inout_clock_out="clk_out")
    fvm.setup_design("toplevel")

def test_add_reset_domain() :
    """Test adding a reset domain. Arguments can be contradictory, as we are just
    testing the interface here."""
    fvm = FvmFramework()
    fvm.add_reset_domain(port_list=["enable"], name="rst", active_high=True,
                         synchronous=True, module="toplevel",
                         asynchronous=True, ignore=True,
                         active_low=True, is_set=True, no_reset=True)
    fvm.setup_design("toplevel")

def test_add_clock() :
    """Test adding a clock. Arguments can be contradictory, as we are just
    testing the interface here."""
    fvm = FvmFramework()
    fvm.add_clock("clk", module="toplevel", period=10, waveform=(3,7),
                  group="clk_in", ignore=True, remove=True, external=True)
    fvm.setup_design("toplevel")

def test_add_reset() :
    """Test adding a reset. Arguments can be contradictory, as we are just
    testing the interface here."""
    fvm = FvmFramework()
    fvm.add_reset("rst", module="toplevel", group="rst_in", ignore=True,
                  remove=True, external=True, active_high=True,
                  active_low=True, asynchronous=True, synchronous=True)
    fvm.setup_design("toplevel")

def test_blackbox() :
    """Test adding a blackbox"""
    fvm = FvmFramework()
    fvm.blackbox("entity")
    fvm.setup_design("toplevel")

def test_blackbox_instance() :
    """Test blackboxing a specific instance"""
    fvm = FvmFramework()
    fvm.blackbox_instance("inst")
    fvm.setup_design("toplevel")

def test_cutpoint() :
    """Test adding a cutpoint. Arguments can be contradictory, as we are just
    testing the interface here."""
    fvm = FvmFramework()
    fvm.cutpoint("signal", module="toplevel", resetval="1111", condition="0000",
                 driver="signal2", wildcards_dont_match_hierarchy_separators=True)
    fvm.setup_design("toplevel")

def test_set_tool_flags() :
    """Test setting tool flags"""
    fvm = FvmFramework()
    fvm.set_tool_flags("xverify", "flag")
    fvm.setup_design("toplevel")

#def test_check_library_exists_false() :
#    fvm = FvmFramework()
#    exists = fvm.check_library_exists("librarythatdoesntexist")
#    assert exists == False

#def test_check_library_exists_true() :
#    fvm = FvmFramework()
#    os.makedirs('test/testlib', exist_ok=True)
#    Path('test/testlib/_info').touch()
#    exists = fvm.check_library_exists("test/testlib")
#    assert exists == True

#def test_cmd_create_library() :
#    fvm = FvmFramework()
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
    """Test logging messages at different levels and checking if errors are
    detected correctly"""
    fvm = FvmFramework()
    fvm.cont = True
    fvm.log(severity, f'Log message with {severity=}')
    retval = fvm.check_errors()
    print(f'{retval=}')
    assert retval == expected

def test_logger_twice() :
    """Test logging messages at different levels and checking if errors are
    detected correctly, even if check_errors() is called multiple times"""
    fvm = FvmFramework()
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
