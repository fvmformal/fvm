from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_systemverilog_source("examples/counter_sv/counter.sv")
fvm.set_toplevel("counter")
fvm.run()
