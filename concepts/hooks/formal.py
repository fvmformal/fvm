from fvm import fvmframework

fvm = fvmframework()
fvm.add_vhdl_sources("examples/dualcounter/*.vhd")
fvm.add_psl_source("examples/dualcounter/dualcounter.psl")
fvm.add_psl_source("examples/countervunit/counter.psl")
fvm.set_toplevel(['counter', 'dualcounter'])
fvm.skip('reachability', 'dualcounter')
fvm.disable_coverage('signoff', 'dualcounter')
fvm.disable_coverage('reachability', 'dualcounter')

# Hooks are functions, so we just have to define them, and then pass them to
# fvm.set_pre_hook() and fvm.set_post_hook()
def my_pre_hook(step, design):
    print(f'**** This is a pre_hook defined by the user! Running before {design}.{step} ****')

def my_post_hook(step, design):
    print(f'**** This is a post_hook defined by the user! Running after {design}.{step} ****')

def my_other_pre_hook(step, design):
    print(f'**** Another pre_hook, running before {design}.{step} ****')

def my_other_post_hook(step, design):
    print(f'**** Another post_hook, running after {design}.{step} ****')

# These hooks are defined for all the designs
fvm.set_pre_hook(my_pre_hook, "lint")
fvm.set_post_hook(my_post_hook, "lint")
fvm.set_pre_hook(my_pre_hook, "prove")
fvm.set_post_hook(my_post_hook, "prove")

# These hooks are only for "dualcounter", and they take priority over the other
# hook defined for all designs
fvm.set_pre_hook(my_other_pre_hook, "prove", "dualcounter")
fvm.set_post_hook(my_other_post_hook, "prove", "dualcounter")

fvm.run()
