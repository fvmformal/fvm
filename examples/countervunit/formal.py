from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples/countervunit/counter.vhd")
fvm.add_psl_source("examples/countervunit/counter_properties.psl")
fvm.set_toplevel("counter")
fvm.run()
