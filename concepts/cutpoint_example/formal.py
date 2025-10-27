from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_source("concepts/cutpoint_example/counter.vhd")
fvm.add_psl_source("concepts/cutpoint_example/counter.psl")
fvm.set_toplevel("counter")
fvm.cutpoint("Q")
fvm.skip("prove.formalcover")
fvm.skip("prove.simcover")
fvm.run()
