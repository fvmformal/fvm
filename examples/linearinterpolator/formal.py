from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/linearinterpolator/*.vhd")
fvm.add_psl_sources("examples/linearinterpolator/*.psl")
fvm.set_toplevel("interpolator")
fvm.run()
