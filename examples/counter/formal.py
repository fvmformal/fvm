from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/counter/counter.vhd")
fvm.set_toplevel("counter")
fvm.run()
