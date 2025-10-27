from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/xor_nn/*.vhd")
fvm.add_psl_sources("examples/xor_nn/*.psl")
fvm.set_toplevel("xor_nn")
fvm.run()
