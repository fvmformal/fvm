from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("concepts/parameterized_sequences/*.psl")
fvm.set_toplevel("uart_tx")
fvm.run()
