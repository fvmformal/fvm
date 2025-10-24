from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_verilog_source("examples/counter_v_psl/counter.v")
fvm.add_psl_source("examples/counter_v_psl/counter_properties.psl")
fvm.set_toplevel("counter")
fvm.run(skip_setup=True)
