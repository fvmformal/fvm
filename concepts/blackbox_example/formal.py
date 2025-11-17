from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
fvm.add_psl_source("concepts/blackbox_instance/dualcounter.psl", flavor="vhdl")
fvm.set_toplevel('dualcounter')
fvm.blackbox('counter')
fvm.skip('reachability')
fvm.skip('rulecheck')
fvm.run()
