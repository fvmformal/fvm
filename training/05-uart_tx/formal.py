from src.builder.framework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("training/05-uart_tx/*.vhd")
fvm.add_psl_sources("training/05-uart_tx/*.psl")
fvm.set_toplevel("uart_tx")
fvm.run()
