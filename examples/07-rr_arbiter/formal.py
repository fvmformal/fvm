from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

os.chdir('open-logic')

fvm.add_vhdl_source("src/base/vhdl/olo_base_arb_prio.vhd")
fvm.add_vhdl_source("src/base/vhdl/olo_base_arb_rr.vhd")
fvm.add_vhdl_source("src/base/vhdl/olo_base_pkg_array.vhd")
fvm.add_vhdl_source("src/base/vhdl/olo_base_pkg_logic.vhd")
fvm.add_vhdl_source("src/base/vhdl/olo_base_pkg_math.vhd")

fvm.add_psl_source("../examples/07-rr_arbiter/olo_base_arb_rr.psl")

fvm.set_toplevel("olo_base_arb_rr")
fvm.add_config("olo_base_arb_rr", "config_width_4", {"Width_g": 4})

fvm.skip("reachability")
fvm.run()
