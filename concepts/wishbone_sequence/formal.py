from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/wishbone_sequence/*.vhd")
fvm.add_psl_sources("concepts/wishbone_sequence/*.psl")
fvm.set_toplevel("wishbone")
fvm.run()
