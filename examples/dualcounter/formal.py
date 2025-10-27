from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/dualcounter/*.vhd")
fvm.add_psl_source("examples/dualcounter/dualcounter_properties.psl")
fvm.set_toplevel('dualcounter')
fvm.skip('reachability')
#fvm.disable_coverage('observability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
#fvm.disable_coverage('bounded_reachability')
fvm.run()
