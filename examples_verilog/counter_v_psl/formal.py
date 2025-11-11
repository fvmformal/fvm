from fvmframework import FvmFramework

fvm = FvmFramework()
fvm.add_verilog_source("examples_verilog/counter_v_psl/counter.v")
fvm.add_psl_source("examples_verilog/counter_v_psl/counter_properties.psl", flavor="verilog")
fvm.set_toplevel("counter")
fvm.run()
