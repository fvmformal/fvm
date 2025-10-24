from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_systemverilog_source("examples/counter_sv_psl/counter.sv")
fvm.add_psl_source("examples/counter_sv_psl/counter_properties.psl")
fvm.set_toplevel("counter")
fvm.run(skip_setup=True)
