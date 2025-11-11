from fvmframework import FvmFramework
import subprocess
import os

fvm = FvmFramework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', '--branch 3.0.1', 'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
fvm.add_vhdl_sources("open-logic/src/axi/vhdl/*.vhd")

fvm.add_psl_source("examples_other/axi_master_simple/olo_axi_master_simple.psl", flavor="vhdl")

fvm.set_toplevel("olo_axi_master_simple")

#fvm.skip('lint')
fvm.skip('friendliness')
fvm.skip('reachability')
#fvm.skip('resets')
#fvm.skip('clocks')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
fvm.skip('prove.simcover')
fvm.run()