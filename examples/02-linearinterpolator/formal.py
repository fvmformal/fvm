from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/02-linearinterpolator/*.vhd")
fvm.add_psl_sources("examples/02-linearinterpolator/*.psl")
fvm.set_toplevel("interpolator")
fvm.run()
