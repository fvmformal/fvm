from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_systemverilog_source("examples_verilog/counter_sv_psl/counter.sv")
fvm.add_psl_source("examples_verilog/counter_sv_psl/counter_properties.psl", flavor="verilog")
fvm.set_toplevel("counter")
fvm.run()
