from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("concepts/transactions_deprecated/*.vhd")
fvm.add_psl_sources("concepts/transactions_deprecated/*.psl")
fvm.set_toplevel("minicalc")
fvm.run()
