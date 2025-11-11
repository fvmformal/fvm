from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("examples_other/synchronizer/synchronizer.vhd")
fvm.add_vhdl_source("examples_other/handshake/handshake.vhd")
fvm.add_psl_source("examples_other/handshake/handshake.psl", flavor="vhdl")
fvm.set_toplevel("handshake")
fvm.run()
