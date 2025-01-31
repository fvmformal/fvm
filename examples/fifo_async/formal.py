from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")

fvm.add_psl_source("examples/fifo_async/olo_base_fifo_async.psl")

fvm.set_toplevel("olo_base_fifo_async")
fvm.add_config("olo_base_fifo_async", "config_width_3_depth_8", {"Width_g": 3, "Depth_g": 8})

fvm.add_clock("In_Clk", period = 10)
fvm.add_clock_domain("In_Clk", ["In_Ready", "In_Rst", "In_Data", "In_Valid"])
fvm.add_clock("Out_Clk", period = 13.5)
fvm.add_clock_domain("Out_Clk", ["Out_Ready", "Out_Rst"])

fvm.add_reset("In_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("In_Rst", ["In_Ready", "In_Rst", "In_Data", "In_Valid"])
fvm.add_reset("Out_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("Out_Rst", ["Out_Ready"])

fvm.skip('reachability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
fvm.run()