from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/04-dualcounter/*.vhd")
fvm.add_psl_source("examples/04-dualcounter/dualcounter.psl")
fvm.set_toplevel('dualcounter')
fvm.skip('reachability')
#fvm.disable_coverage('observability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
#fvm.disable_coverage('bounded_reachability')
fvm.run()
