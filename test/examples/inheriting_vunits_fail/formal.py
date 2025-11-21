from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/uart_tx/*.vhd")
fvm.add_psl_sources("test/examples/inheriting_vunits_fail/*.psl", flavor="vhdl")
fvm.set_toplevel("uart_tx")

# There is a failure in prove.formalcover
# fvm.allow_failure("prove.formalcover")
fvm.allow_failure("prove.simcover")
fvm.run()
