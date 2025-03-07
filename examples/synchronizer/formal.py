from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/synchronizer/synchronizer.vhd")
fvm.set_toplevel("synchronizer")
fvm.run()
