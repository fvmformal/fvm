from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("concepts/parameterized_properties/*.psl")
fvm.set_toplevel("uart_tx")
fvm.allow_failure("prove.formalcover")
fvm.allow_failure("prove.simcover")
fvm.run()
