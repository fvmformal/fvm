from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
fvm.add_vhdl_source("open-logic/src/axi/vhdl/olo_axi_pkg_protocol.vhd")
fvm.add_vhdl_source("open-logic/src/axi/vhdl/olo_axi_lite_slave.vhd")

fvm.add_psl_source("examples/axi_lite_slave/olo_axi_lite_slave.psl")

fvm.set_toplevel("olo_axi_lite_slave")

fvm.skip('lint')
fvm.skip('friendliness')
fvm.skip('reachability')
fvm.skip('resets')
fvm.skip('clocks')
fvm.run()