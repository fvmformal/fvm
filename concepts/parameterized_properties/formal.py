from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/05-uart_tx/*.vhd")
fvm.add_psl_sources("concepts/parameterized_properties/*.psl")
fvm.set_toplevel("uart_tx")
fvm.run()
