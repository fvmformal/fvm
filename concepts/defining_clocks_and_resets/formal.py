from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/counter/*.vhd")
fvm.add_psl_source("examples/counter/counter_properties.psl", flavor="vhdl")
fvm.set_toplevel("counter")
fvm.add_clock("clk")
fvm.add_clock_domain(["Q", "rst"], "clk")
fvm.add_reset("rst", asynchronous=True, active_high=True)
fvm.add_reset_domain(["Q"], "rst")
fvm.run()

