from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/wishbone_sequence/*.vhd")
fvm.add_psl_sources("concepts/wishbone_sequence/*.psl", flavor="vhdl")
fvm.set_toplevel("wishbone")
fvm.run()
