from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("examples/00-counter/counter.vhd")
fvm.set_toplevel("counter")
fvm.run()
#fvm.setup()
#fvm.run_step("reachability")
