# Toolchain definitions file

# Currently, only the Questa tools are supported

# Each toolchain may have different tools to solve different problemsa
#
# For the Questa tools, each tool is run through a wrapper which is the actual
# command that must be run in the command-line
QUESTA_TOOLS = {
        # step           : ["tool",       "wrapper"],
        "lint"           : ["lint",       "qverify"],
        "friendliness"   : ["autocheck",  "qverify"],
        "rulecheck"      : ["autocheck",  "qverify"],
        "xverify"        : ["xcheck",     "qverify"],
        "reachability"   : ["covercheck", "qverify"],
        "fault"          : ["slec",       "qverify"],
        "resets"         : ["rdc",        "qverify"],
        "clocks"         : ["cdc",        "qverify"],
        "prove"          : ["propcheck",  "qverify"],
#        "simulate"       : ["vsim", "vsim"],
#        "createemptylib" : ["vlib", "vlib"],
#        "compilevhdl"    : ["vcom", "vcom"],
#        "compileverilog" : ["vlog", "vlog"],
        }

# Each toolchain has a set of tools assigned
TOOLS = {
        "questa" : QUESTA_TOOLS
        }

default_flags = {
        "questa" : {
                   "lint methodology" : "ip -goal start",
                   "autocheck verify" : "",
                   "xcheck verify" : "",
                   "covercheck verify" : "",
                   "rdc generate report" : "-resetcheck",
                   "cdc generate report" : "-clockcheck",
                   "formal verify" : "-justify_initial_x -auto_constraint_off",
                   }
        }

import os

def get_toolchain():
    """Get the toolchain from a specific environment variable. In the future,
    if the environment variable is not set, we plan to auto-detect which tools
    are available in the PATH and assign the first we find (with some
    priority)"""
    default = 'questa'
    toolchain = os.getenv('FVM_TOOLCHAIN', default)
    return toolchain

def get_default_flags(toolchain):
    return default_flags[toolchain]

