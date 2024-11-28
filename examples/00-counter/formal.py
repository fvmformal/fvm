from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/00-counter/counter.vhd")
fvm.set_toplevel("counter")
fvm.run()
