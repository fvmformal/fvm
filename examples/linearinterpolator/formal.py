from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/linearinterpolator/*.vhd")
fvm.add_psl_sources("examples/linearinterpolator/*.psl")
fvm.set_toplevel("interpolator")
# TODO : evaluate in detail if what RDC/CDC is seeing is a problematic issue or
# not, if it can be denoted to warning, etc
fvm.skip("resets")
fvm.skip("clocks")
fvm.run()
