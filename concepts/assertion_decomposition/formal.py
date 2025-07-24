from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/linearinterpolator/*.vhd")
fvm.add_psl_sources("concepts/assertion_decomposition/*.psl")
fvm.set_toplevel("interpolator")

fvm.add_clock("clk", period = 10)
fvm.add_clock_domain("clk", ["inferior", "superior", "valid"])

fvm.add_reset("rst", asynchronous=True, active_high=True)
fvm.add_reset_domain("rst", ["inferior", "superior", "valid"])

fvm.run()
