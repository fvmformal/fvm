from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("concepts/counter_abstraction/counter.vhd")
fvm.add_psl_source("concepts/counter_abstraction/counter.psl", flavor="vhdl")
fvm.set_toplevel("counter")
fvm.cutpoint("Q")
fvm.set_timeout("rulecheck", "1m")
fvm.set_timeout("reachability", "1m")
fvm.set_coverage_goal("reachability", 0)
fvm.skip("prove.formalcover")
fvm.skip("prove.simcover")
fvm.run()
