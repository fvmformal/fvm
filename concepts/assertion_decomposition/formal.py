from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/linearinterpolator/*.vhd")
fvm.add_psl_sources("concepts/assertion_decomposition/*.psl")
fvm.set_toplevel("interpolator")

fvm.add_clock("clk", period = 10)
fvm.add_clock_domain(["inferior", "superior", "valid"], clock_name="clk")

fvm.add_reset("rst", asynchronous=True, active_high=True)
fvm.add_reset_domain(["inferior", "superior", "valid"], name="rst")

fvm.run()
