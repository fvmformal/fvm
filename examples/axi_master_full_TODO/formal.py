from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
fvm.add_vhdl_source("open-logic/src/axi/vhdl/olo_axi_pkg_protocol.vhd")
fvm.add_vhdl_source("open-logic/src/axi/vhdl/olo_axi_master_simple.vhd")
fvm.add_vhdl_source("open-logic/src/axi/vhdl/olo_axi_master_full.vhd")

fvm.add_psl_source("examples/axi_master_full/olo_axi_master_full.psl")

fvm.set_toplevel("olo_axi_master_full")

fvm.add_clock("Clk")
fvm.add_clock_domain("Clk", ["CmdRd_Ready", "Rst"])
fvm.add_reset("Rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("Rst", ["CmdRd_Ready"])

fvm.skip('reachability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
fvm.run()
