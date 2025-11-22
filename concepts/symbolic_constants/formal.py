from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("concepts/inheriting_vunits/uart_tx_sequence.psl", flavor="vhdl")
fvm.add_psl_sources("concepts/symbolic_constants/uart_tx.psl", flavor="vhdl")
fvm.set_toplevel("uart_tx")
fvm.set_coverage_goal("prove.formalcover", 0)
fvm.skip("prove.simcover")
fvm.run()
