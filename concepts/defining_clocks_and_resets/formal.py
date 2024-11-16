from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/01-countervunit/*.vhd")
fvm.add_psl_source("examples/01-countervunit/counter.psl")
fvm.set_toplevel("counter")
fvm.add_clock("clk")
fvm.add_clock_domain("clk", ["Q", "rst"])
fvm.add_reset("rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("rst", ["Q"])
fvm.run()

