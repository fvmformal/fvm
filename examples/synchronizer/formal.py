from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples/synchronizer/synchronizer.vhd")
fvm.add_psl_source("examples/synchronizer/synchronizer.psl")
fvm.set_toplevel("synchronizer")
fvm.run()
