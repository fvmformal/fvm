# Toolchain defintions file

# Currently, only the questa tools are supported

# Each toolchain may have different tools to solve different problems
QUESTA_TOOLS = {
        "friendliness"   : "covercheck",
        "rulecheck"      : "autocheck",
        "prove"          : "qverify",
        "lint"           : "qverify",
        "simulate"       : "vsim",
        "createemptylib" : "vlib",
        "compilevhdl"    : "vcom",
        "compileverilog" : "vlog"
        }

# Each toolchain has a set of tools assigned
TOOLS = {
        "questa" : QUESTA_TOOLS
        }

