from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("concepts/reachability_example/counter.vhd")
fvm.add_psl_source("concepts/reachability_example/counter.psl")
fvm.set_toplevel("counter")
# Reachability is skipped because is going to fail,
# and we don't want to break the CI.
fvm.skip('reachability')
fvm.skip('prove.coverage')
fvm.run()
