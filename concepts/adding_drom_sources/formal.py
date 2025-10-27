from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/wishbone_sequence/*.vhd")
fvm.add_psl_source("concepts/wishbone_sequence/properties.psl")
fvm.add_drom_source("drom/wishbone_classic_read.json")
fvm.set_toplevel("wishbone")
fvm.allow_failure("rulecheck")
fvm.set_coverage_goal("reachability", 75)
fvm.set_coverage_goal("prove.formalcover", 0)
fvm.run()
