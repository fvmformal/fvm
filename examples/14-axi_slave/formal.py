from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

os.chdir('open-logic')

fvm.add_vhdl_sources("src/base/vhdl/*.vhd")
fvm.add_vhdl_source("src/axi/vhdl/olo_axi_pkg_protocol.vhd")
fvm.add_vhdl_source("src/axi/vhdl/olo_axi_lite_slave.vhd")

fvm.add_psl_source("../examples/14-axi_slave/olo_axi_lite_slave.psl")

fvm.set_toplevel("olo_axi_lite_slave")

fvm.skip("reachability")
fvm.run()
