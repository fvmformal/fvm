from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/05-uart_tx/*.vhd")
fvm.add_psl_sources("concepts/inheriting_vunits/uart_tx_sequence.psl")
fvm.add_psl_sources("concepts/symbolic_constants/uart_tx.psl")
fvm.set_toplevel("uart_tx")
fvm.run()
