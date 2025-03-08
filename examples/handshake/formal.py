from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/synchronizer/synchronizer.vhd")
fvm.add_vhdl_source("examples/handshake/handshake.vhd")
fvm.add_psl_source("examples/handshake/handshake.psl")
fvm.set_toplevel("handshake")
fvm.run()
