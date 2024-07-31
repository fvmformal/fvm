from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/05-uart_tx/*.vhd")
fvm.add_psl_sources("examples/05-uart_tx/*.psl")
fvm.list_sources()
fvm.set_toplevel("uart_tx")
fvm.setup()
fvm.run()
fvm.check_errors()
