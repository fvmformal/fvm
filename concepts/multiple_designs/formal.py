from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/dualcounter/*.vhd")
fvm.add_psl_source("examples/dualcounter/dualcounter_properties.psl", flavor="vhdl")
fvm.add_psl_source("examples/counter/counter_properties.psl", flavor="vhdl")
fvm.set_toplevel(['counter', 'dualcounter'])
fvm.skip('reachability', 'dualcounter')
fvm.disable_coverage('signoff', 'dualcounter')
fvm.disable_coverage('reachability', 'dualcounter')
fvm.run()
