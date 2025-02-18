from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', '--branch', '3.0.1', 'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_arb_prio.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_arb_rr.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_array.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_logic.vhd")
fvm.add_vhdl_source("open-logic/src/base/vhdl/olo_base_pkg_math.vhd")

fvm.add_psl_sources("examples/arbiter_rr/*.psl")

fvm.set_toplevel("olo_base_arb_rr")
fvm.add_config("olo_base_arb_rr", "config_width_4", {"Width_g": 4})

fvm.skip("reachability")
fvm.skip('prove.formalcover')
fvm.run()
