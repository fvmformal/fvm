from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_verilog_source("examples/counter_v/counter.v")
fvm.add_systemverilog_source("examples/counter_v/counter_properties.sv")
fvm.set_toplevel("counter")
fvm.run(skip_setup=True)
