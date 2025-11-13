from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("concepts/reachability_example/counter.vhd")
fvm.add_psl_sources("concepts/reachability_example/*.psl", flavor="vhdl")
fvm.set_toplevel("counter")
fvm.set_coverage_goal("reachability", 85)
fvm.set_coverage_goal("prove.simcover", 85)
fvm.run()
