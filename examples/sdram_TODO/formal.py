from fvm import fvmframework
import subprocess
import os
import re

fvm = fvmframework()

subprocess.run(['git', 'clone', 
'https://github.com/nullobject/sdram-fpga'])

fvm.add_vhdl_source('sdram-fpga/sdram.vhd')

fvm.add_psl_source("examples/sdram_TODO/sdram.psl")

fvm.set_toplevel("sdram")
fvm.add_config("sdram", "sdram_clock_100_MHz", {"CLK_FREQ": 100})

fvm.skip("reachability")
#fvm.disable_coverage('observability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
#fvm.disable_coverage('bounded_reachability')
fvm.run()
