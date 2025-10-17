from fvm import FvmFramework
import subprocess
import os

fvm = FvmFramework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/VLSI-EDA/PoC'])

fvm.add_vhdl_source("PoC/src/common/utils.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/vectors.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/strings.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/config.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/components.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/physical.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/common/my_config.vhdl.template","PoC")
fvm.add_vhdl_sources("PoC/src/common/my_project.vhdl.template","PoC")
fvm.add_vhdl_sources("PoC/src/io/io.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/net/net.pkg.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/net/ipv6/ipv6_TX.vhdl","PoC")

fvm.add_psl_sources("examples/ipv6TX/*.psl")

fvm.set_toplevel("PoC.ipv6_TX")

fvm.skip('rulecheck')
fvm.skip('reachability')
fvm.skip('resets')
fvm.skip('clocks')
fvm.skip('prove.formalcover')
fvm.skip('prove.simcover')
fvm.run()
