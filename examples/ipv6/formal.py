from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/VLSI-EDA/PoC'])

# We change the VHDL files using the vhdl_changes.py script
# from the same directory. We had to change a few lines in 
# the PoC source code to make it work (because of compilation
# errors) but it wasn't really important, except for the bug 
# we found in ipv6_Wrapper.vhdl
import vhdl_changes

fvm.add_vhdl_source("PoC/src/common/utils.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/vectors.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/strings.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/config.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/components.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/common/physical.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/common/my_config.vhdl.template","PoC")
fvm.add_vhdl_sources("PoC/src/common/my_project.vhdl.template","PoC")
fvm.add_vhdl_source("PoC/src/bus/stream/stream_Buffer.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/bus/stream/stream_Mux.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/bus/stream/stream_DeMux.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/fifo/fifo_cc_got.vhdl","PoC")
fvm.add_vhdl_source("PoC/src/fifo/fifo_cc_got_tempgot.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/mem/ocram/ocram.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/mem/ocram/ocram_sp.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/mem/ocram/ocram_sdp.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/arith/arith.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/arith/arith_carrychain_inc.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/arith/arith_prefix_and.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/mem/mem.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/io/io.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/net/net.pkg.vhdl","PoC")
fvm.add_vhdl_sources("PoC/src/net/ipv6/*.vhdl","PoC")

fvm.add_psl_sources("examples/ipv6/*.psl")

fvm.set_toplevel("PoC.ipv6_Wrapper")

#fvm.skip('lint')
#fvm.skip('friendliness')
#fvm.skip('rulecheck')
fvm.timeout('rulecheck', "1m")
fvm.allow_failure('rulecheck')
#fvm.skip('reachability')
fvm.allow_failure('reachability')
#fvm.skip('resets')
#fvm.skip('clocks')
#fvm.skip('prove.formalcover')
fvm.allow_failure('prove.formalcover')
fvm.skip('prove.simcover')
fvm.run()
