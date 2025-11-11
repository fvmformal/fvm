from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("concepts/user_defined_hdltypes/colors.vhd")
fvm.add_psl_source("concepts/user_defined_hdltypes/colors.psl", flavor="vhdl")
fvm.set_toplevel("colors")
fvm.allow_failure("prove.formalcover")
fvm.allow_failure("prove.simcover")
fvm.run()
