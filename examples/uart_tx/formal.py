from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("examples/uart_tx/*.psl", flavor="vhdl")
fvm.add_drom_sources("examples/uart_tx/*.json", flavor="vhdl")
fvm.set_toplevel("uart_tx")
# Rulecheck fails due to symbolic constants are interpreted as
# declaration undriven.
fvm.allow_failure("rulecheck")
fvm.allow_failure("prove.simcover")
fvm.run()
