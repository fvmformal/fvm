from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/countervunit_var/counter.vhd")
fvm.add_psl_source("examples/countervunit_var/counter.psl")
fvm.set_toplevel("counter")
fvm.run()
