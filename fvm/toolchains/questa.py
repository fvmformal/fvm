from fvm.steps import steps

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

def setup_lint():
    print("**** setup lint ****")
    pass

def run_lint():
    print("**** run lint ****")
    pass

def setup_friendliness():
    print("**** setup friendliness ****")
    pass

def run_friendliness():
    print("**** run friendliness ****")
    pass

def setup_rulecheck():
    print("**** setup rulecheck ****")
    pass

def run_rulecheck():
    print("**** run rulecheck ****")
    pass

def setup_xverify():
    print("**** setup xverify ****")
    pass

def run_xverify():
    print("**** run xverify ****")
    pass

def setup_reachability():
    print("**** setup reachability ****")
    pass

def run_reachability():
    print("**** run reachability ****")
    pass

def setup_fault():
    print("**** setup fault ****")
    pass

def run_fault():
    print("**** run fault ****")
    pass

def setup_resets():
    print("**** setup resets ****")
    pass

def run_resets():
    print("**** run resets ****")
    pass

def setup_clocks():
    print("**** setup clocks ****")
    pass

def run_clocks():
    print("**** run clocks ****")
    pass

def setup_resets():
    print("**** setup resets ****")
    pass

def run_resets():
    print("**** run resets ****")
    pass

def setup_prove():
    print("**** setup prove ****")
    pass

def run_prove():
    print("**** run prove ****")
    pass

def setup_prove_simcover():
    print("**** setup prove_simcover ****")
    pass

def run_prove_simcover():
    print("**** run prove_simcover ****")
    pass

def setup_prove_formalcover():
    print("**** setup prove_formalcover ****")
    pass

def run_prove_formalcover():
    print("**** run prove_formalcover ****")
    pass

def define_steps(steps):
    steps.add_step('lint', setup_lint, run_lint)
    steps.add_step('friendliness', setup_friendliness, run_friendliness)
    steps.add_step('rulecheck', setup_rulecheck, run_rulecheck)
    steps.add_step('xverify', setup_xverify, run_xverify)
    steps.add_step('reachability', setup_reachability, run_reachability)
    steps.add_step('fault', setup_fault, run_fault)
    steps.add_step('resets', setup_resets, run_resets)
    steps.add_step('clocks', setup_clocks, run_clocks)
    steps.add_step('prove', setup_prove, run_prove)
    steps.add_post_step('prove', 'simcover', setup_prove_simcover, run_prove_simcover)
    steps.add_post_step('prove', 'formalcover', setup_prove_formalcover, run_prove_formalcover)

