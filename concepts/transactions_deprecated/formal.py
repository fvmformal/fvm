from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/transactions_deprecated/*.vhd")
fvm.add_psl_sources("concepts/transactions_deprecated/*.psl", flavor="vhdl")
fvm.set_toplevel("minicalc")
fvm.allow_failure("prove.simcover")
fvm.run()
