from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples_other/xor_nn/*.vhd")
fvm.add_psl_sources("examples_other/xor_nn/*.psl", flavor="vhdl")
fvm.set_toplevel("xor_nn")
fvm.run()
