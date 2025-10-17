from fvm import FvmFramework
import subprocess
import os

fvm = FvmFramework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', '--branch', '3.0.1', 'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")

fvm.add_psl_source("examples/fifo_async/olo_base_fifo_async.psl")

fvm.set_toplevel("olo_base_fifo_async")
fvm.add_config("olo_base_fifo_async", "config_width_3_depth_8", {"Width_g": 3, "Depth_g": 8})

if fvm.toolchain == "sby":
    fvm.set_tool_flags("ghdl", fvm.get_tool_flags("ghdl") + " -frelaxed")

fvm.add_clock("In_Clk", period = 10)
fvm.add_clock_domain(["In_Ready", "In_Rst", "In_Data", "In_Valid"], clock_name="In_Clk")
fvm.add_clock("Out_Clk", period = 13.5)
fvm.add_clock_domain(["Out_Ready", "Out_Rst"], clock_name="Out_Clk")

fvm.add_reset("In_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain(["In_Ready", "In_Rst", "In_Data", "In_Valid"], name="In_Rst")
fvm.add_reset("Out_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain(["Out_Ready"], name="Out_Rst")

fvm.allow_failure("xverify")
fvm.set_coverage_goal("reachability", 80)
fvm.set_coverage_goal("prove.formalcover", 60)
fvm.skip('prove.simcover')
fvm.run()
