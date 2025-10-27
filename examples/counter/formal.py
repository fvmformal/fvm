from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples/counter/counter.vhd")
fvm.set_toplevel("counter")
fvm.run()
