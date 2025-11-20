from fvm import FvmFramework
import subprocess
import os

fvm = FvmFramework()

subprocess.run(['git', 'clone', 
'https://github.com/nullobject/sdram-fpga'])

fvm.add_vhdl_source("sdram-fpga/sdram.vhd")
fvm.add_psl_sources("examples/sdram/*.psl", flavor="vhdl")
fvm.add_drom_sources("examples/sdram/*.json", flavor="vhdl")

fvm.set_toplevel("sdram")
fvm.add_config("sdram", "config_freq_10_desl_200", {"CLK_FREQ": 10.0, "T_DESL": 200.0})

fvm.allow_failure('rulecheck')
fvm.allow_failure('xverify')
fvm.set_coverage_goal('reachability', 75)

fvm.skip('prove.simcover')
fvm.run()