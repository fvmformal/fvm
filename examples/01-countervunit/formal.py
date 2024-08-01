from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/01-countervunit/counter.vhd")
fvm.add_psl_source("examples/01-countervunit/counter.psl")
fvm.set_toplevel("counter")
fvm.run()
