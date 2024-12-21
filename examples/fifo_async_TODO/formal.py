from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_fifo_async.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_array.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_logic.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_math.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_cc_bits.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_cc_reset.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_ram_sdp.vhd")


fvm.add_psl_source("examples/fifo_async/olo_base_fifo_async.psl")

fvm.set_toplevel("olo_base_fifo_async")
fvm.add_config("olo_base_fifo_async", "config_width_3_latency_0", {"Width_g": 3, "Depth_g": 2})

fvm.add_clock("In_Clk")
fvm.add_clock_domain("In_Clk", ["In_Ready", "In_Rst"])
fvm.add_clock("Out_Clk")
fvm.add_clock_domain("Out_Clk", ["Out_Ready", "Out_Rst"])

fvm.add_reset("In_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("In_Rst", ["In_Ready"])
fvm.add_reset("Out_Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("Out_Rst", ["Out_Ready"])

fvm.skip('lint')
#fvm.skip('friendliness')
fvm.skip('reachability')
fvm.skip('resets')
fvm.skip('clocks')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
fvm.run()
