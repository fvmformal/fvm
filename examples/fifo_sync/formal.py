from fvm import FvmFramework
import subprocess
import os

fvm = FvmFramework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', '--branch', '3.0.1', 'https://github.com/open-logic/open-logic'])

fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
fvm.add_vhdl_sources("examples/fifo_sync/*.vhd")

fvm.add_psl_sources("examples/fifo_sync/*.psl")

fvm.set_toplevel("olo_base_fifo_sync")
fvm.add_config("olo_base_fifo_sync", "config_width_3_depth_8", {"Width_g": 3, "Depth_g": 8})

if fvm.toolchain == "sby":
    fvm.set_tool_flags("ghdl", fvm.get_tool_flags("ghdl") + " -frelaxed")

fvm.allow_failure('xverify')

fvm.set_coverage_goal('reachability', 70)
fvm.set_coverage_goal('prove.formalcover', 80)
fvm.set_coverage_goal('prove.simcover', 70)

fvm.run()
