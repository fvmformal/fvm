from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("test/examples/counter_psl_in_vhdl/counter.vhd")
fvm.set_toplevel("counter")
fvm.run()
