from fvm import FvmFramework

fvm = FvmFramework()
fvm.add_vhdl_sources("examples/countervunit/*.vhd")
fvm.add_psl_source("examples/countervunit/counter_properties.psl", flavor="vhdl")
fvm.set_toplevel("counter")
fvm.add_config("counter", "max_count_128", dict(MAX_COUNT=128))
fvm.add_config("counter", "max_count_200", dict(MAX_COUNT=200))
fvm.add_config("counter", "max_count_255", dict(MAX_COUNT=255))
fvm.run()
