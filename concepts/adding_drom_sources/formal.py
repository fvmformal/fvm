from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("concepts/wishbone_sequence/*.vhd")
fvm.add_psl_source("concepts/wishbone_sequence/properties.psl")
fvm.add_drom_source("drom/wishbone_classic_read.json")
fvm.set_toplevel("wishbone")
fvm.run()
