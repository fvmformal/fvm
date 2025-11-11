from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples_other/countervunit_var/counter.vhd")
fvm.add_psl_source("examples_other/countervunit_var/counter.psl", flavor="vhdl")
fvm.set_toplevel("counter")
fvm.run()
