from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', 'git@github.com:gabrieljcs/ann-vhdl.git'])

fvm.add_vhdl_sources("ann-vhdl/src/*.vhd")

#fvm.add_psl_sources("examples/ann-vhdl/*.psl")

fvm.set_toplevel("network")

fvm.run()
