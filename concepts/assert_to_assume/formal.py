from fvmframework import FvmFramework

# Prove properties of counter
fvm = FvmFramework()
fvm.add_vhdl_source("examples/dualcounter/counter.vhd")
fvm.add_psl_source("concepts/assert_to_assume/counter_properties.psl", flavor="vhdl")
fvm.add_psl_source("concepts/assert_to_assume/counter_assert.psl", flavor="vhdl")
fvm.set_toplevel('counter')
fvm.run()

# Prove properties for dualcounter
fvm.clear_psl_sources()
fvm.add_vhdl_source("concepts/assert_to_assume/dualcounter.vhd")
fvm.add_psl_source("concepts/assert_to_assume/counter_properties.psl", flavor="vhdl")
fvm.add_psl_source("concepts/assert_to_assume/counter_assert_to_assume.psl", flavor="vhdl")
fvm.add_psl_source("concepts/assert_to_assume/dualcounter_properties.psl", flavor="vhdl")
fvm.set_toplevel('dualcounter')
fvm.skip('reachability')
#fvm.disable_coverage('observability')
fvm.disable_coverage('signoff')
fvm.disable_coverage('reachability')
#fvm.disable_coverage('bounded_reachability')
fvm.run()
