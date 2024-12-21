from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/hdl-modules/hdl-modules'])

os.chdir('hdl-modules')

fvm.add_vhdl_source("modules/common/src/attribute_pkg.vhd")
fvm.add_vhdl_source("modules/common/src/types_pkg.vhd")
fvm.add_vhdl_sources("modules/math/src/*.vhd")
fvm.add_vhdl_sources("modules/lfsr/src/*.vhd")
fvm.add_vhdl_sources("modules/sine_generator/src/*.vhd")

fvm.add_psl_source("../examples/sine_generator_TODO/sine_generator.psl")

fvm.set_toplevel("sine_generator")
fvm.add_config("sine_generator", "config_width_8_latency_0", {"memory_data_width": 8, "memory_address_width": 16})

fvm.run()
