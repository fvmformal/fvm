from src.builder.framework import fvmframework

fvm = fvmframework(loglevel="TRACE")
fvm.add_vhdl_source("examples/00-counter/counter.vhd")
fvm.list_sources()
fvm.set_toplevel("counter")
fvm.setup()
#fvm.run()
fvm.run_step("lint")
fvm.run_step("prove")
fvm.check_errors()

