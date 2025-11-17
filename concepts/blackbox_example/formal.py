from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
fvm.add_psl_source("concepts/blackbox_instance/dualcounter.psl", flavor="vhdl")
fvm.set_toplevel('dualcounter')
fvm.blackbox('counter')
fvm.skip('reachability')
fvm.skip('rulecheck')
fvm.set_coverage_goal('prove.formalcover', 0)
fvm.set_coverage_goal('prove.simcover', 0)
fvm.run()
