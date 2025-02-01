from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("concepts/inheriting_vunits/uart_tx_sequence.psl")
fvm.add_psl_sources("concepts/symbolic_constants/uart_tx.psl")
fvm.set_toplevel("uart_tx")
# We need to skip the simcover step because QuestaSim does not support the
# restrict() PSL directive
fvm.skip("prove.coverage")
fvm.skip("prove.simcover")
fvm.run()
