from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("concepts/user_defined_hdltypes_in_package/*.vhd")
fvm.add_psl_source("concepts/user_defined_hdltypes_in_package/colors.psl", flavor="vhdl")
fvm.set_toplevel("colors")
fvm.allow_failure("prove.formalcover")
fvm.allow_failure("prove.simcover")
fvm.run()
