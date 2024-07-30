from src.builder.framework import fvmframework

fvm = fvmframework(loglevel="TRACE")
fvm.add_vhdl_sources("concepts/transactions/*.vhd")
fvm.add_psl_sources("concepts/transactions/*.psl")
fvm.list_sources()
fvm.set_toplevel("minicalc")
fvm.setup()
fvm.run()
fvm.check_errors()
