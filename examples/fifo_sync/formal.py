from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")

fvm.add_psl_sources("examples/fifo_sync/*.psl")

fvm.set_toplevel("olo_base_fifo_sync")
fvm.add_config("olo_base_fifo_sync", "config_width_3_depth_2", {"Width_g": 3, "Depth_g": 8})

fvm.skip('lint')
fvm.skip('friendliness')
fvm.skip('reachability')
fvm.skip('resets')
fvm.skip('clocks')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
fvm.run()
