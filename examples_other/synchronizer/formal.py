from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples_other/synchronizer/synchronizer.vhd")
fvm.add_psl_source("examples_other/synchronizer/synchronizer.psl", flavor="vhdl")
fvm.set_toplevel("synchronizer")
fvm.run()
