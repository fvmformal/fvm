from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/adding_drom_sources/*.vhd")
fvm.add_psl_source("concepts/adding_drom_sources/properties.psl", flavor="vhdl")
fvm.add_drom_source("drom_sequences/wishbone_classic_read.json", flavor="vhdl")
fvm.set_toplevel("wishbone")
fvm.allow_failure("rulecheck")
fvm.set_coverage_goal("reachability", 75)
fvm.skip("prove.formalcover")
fvm.run()
