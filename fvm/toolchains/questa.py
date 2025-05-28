# For the Questa tools, each tool is run through a wrapper which is the actual
# command that must be run in the command-line
tools = {
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

# Set sensible default options for the tools
default_flags = {
        "lint methodology" : "ip -goal start",
        "autocheck verify" : "",
        "xcheck verify" : "",
        "covercheck verify" : "",
        "rdc generate report" : "-resetcheck",
        "cdc generate report" : "-clockcheck",
        "formal verify" : "-justify_initial_x -auto_constraint_off",
        }

