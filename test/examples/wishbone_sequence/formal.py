from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/adding_drom_sources/*.vhd")
fvm.add_psl_source("concepts/adding_drom_sources/properties.psl", flavor="vhdl")
fvm.add_psl_source("test/examples/wishbone_sequence/wishbone_classic_read.psl", flavor="vhdl")
fvm.set_toplevel("wishbone")
fvm.skip("rulecheck")
fvm.set_coverage_goal("reachability", 70)
fvm.skip("prove.formalcover")
fvm.run()
