from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_source("concepts/user_defined_hdltypes/colors.vhd")
fvm.add_psl_source("concepts/user_defined_hdltypes/colors.psl")
fvm.set_toplevel("colors")
fvm.run()
