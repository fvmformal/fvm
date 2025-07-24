from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/linearinterpolator/*.vhd")
fvm.add_psl_sources("concepts/assertion_decomposition/*.psl")
fvm.set_toplevel("interpolator")
fvm.run()
