# Toolchain defintions file

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

