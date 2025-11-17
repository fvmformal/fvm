from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/wishbone_sequence/*.vhd")
fvm.add_psl_sources("concepts/wishbone_sequence/*.psl", flavor="vhdl")
fvm.set_toplevel("wishbone")
fvm.skip("rulecheck")
fvm.set_coverage_goal("reachability", 70)
fvm.skip("prove.formalcover")
fvm.run()
