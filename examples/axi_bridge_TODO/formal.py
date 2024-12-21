from fvm import fvmframework
import subprocess
import os

fvm = fvmframework()

subprocess.run(['git', 'clone', '--recurse-submodules=:src', 
'https://github.com/slaclab/surf'])

fvm.add_vhdl_source("surf/base/general/rtl/StdRtlPkg.vhd")
fvm.add_vhdl_source("surf/base/general/rtl/TextUtilPkg.vhd")
fvm.add_vhdl_source("surf/axi/axi-lite/rtl/AxiLitePkg.vhd")
fvm.add_vhdl_source("surf/axi/axi4/rtl/AxiPkg.vhd")
fvm.add_vhdl_source("surf/axi/bridge/rtl/AxiToAxiLite.vhd")

fvm.set_toplevel("AxiToAxiLite")

fvm.run()
