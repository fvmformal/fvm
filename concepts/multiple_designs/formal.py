from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/dualcounter/*.vhd")
fvm.add_psl_source("examples/dualcounter/dualcounter_properties.psl")
fvm.add_psl_source("examples/countervunit/counter_properties.psl")
fvm.set_toplevel(['counter', 'dualcounter'])
fvm.skip('reachability', 'dualcounter')
fvm.disable_coverage('signoff', 'dualcounter')
fvm.disable_coverage('reachability', 'dualcounter')
fvm.run()
