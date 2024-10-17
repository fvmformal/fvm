from src.builder.framework import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("concepts/user_defined_hdltypes_in_package/*.vhd")
fvm.add_psl_source("concepts/user_defined_hdltypes_in_package/colors.psl")
fvm.set_toplevel("colors")
fvm.run()
