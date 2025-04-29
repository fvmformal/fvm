from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
fvm.add_psl_source("concepts/blackbox_instance/dualcounter.psl")
fvm.set_toplevel('dualcounter')
fvm.blackbox('counter')
#fvm.skip('reachability')
#fvm.disable_coverage('observability')
#fvm.disable_coverage('signoff')
#fvm.disable_coverage('reachability')
#fvm.disable_coverage('bounded_reachability')
fvm.run()
