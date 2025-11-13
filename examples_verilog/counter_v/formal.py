from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_verilog_source("examples_verilog/counter_v/counter.v")
fvm.add_systemverilog_source("examples_verilog/counter_v/counter_properties.sv")
fvm.set_toplevel("counter")
fvm.log("error", "Not working since binding is not supported yet")
# This example doesn't work since binding is not supported yet
fvm.run()
