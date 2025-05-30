from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/countervunit/*.vhd")
fvm.add_psl_source("examples/countervunit/counter_properties.psl")
fvm.set_toplevel("counter")
fvm.add_clock("clk")
fvm.add_clock_domain("clk", ["Q", "rst"])
fvm.add_reset("rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("rst", ["Q"])
fvm.run()

