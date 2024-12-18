from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

os.chdir('open-logic')

fvm.add_vhdl_sources("src/base/vhdl/*.vhd")
fvm.add_vhdl_source("src/axi/vhdl/olo_axi_pkg_protocol.vhd")
fvm.add_vhdl_source("src/axi/vhdl/olo_axi_master_simple.vhd")
fvm.add_vhdl_source("src/axi/vhdl/olo_axi_master_full.vhd")

fvm.add_psl_source("../examples/11-axi_master_full/olo_axi_master_full.psl")

fvm.set_toplevel("olo_axi_master_full")

fvm.run()
