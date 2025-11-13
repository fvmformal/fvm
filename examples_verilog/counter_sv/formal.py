from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_systemverilog_source("examples_verilog/counter_sv/counter.sv")
fvm.set_toplevel("counter")
fvm.run()
