from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("concepts/reachability_example/counter.vhd")
fvm.add_psl_source("concepts/reachability_example/counter.psl")
fvm.set_toplevel("counter")
#fvm.skip('reachability')
fvm.run()
