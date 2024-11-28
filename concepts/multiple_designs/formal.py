from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/04-dualcounter/*.vhd")
fvm.add_psl_source("examples/04-dualcounter/dualcounter.psl")
fvm.add_psl_source("examples/01-countervunit/counter.psl")
fvm.set_toplevel(['counter', 'dualcounter'])
fvm.skip('reachability', 'dualcounter')
fvm.disable_coverage('signoff', 'dualcounter')
fvm.disable_coverage('reachability', 'dualcounter')
fvm.run()
