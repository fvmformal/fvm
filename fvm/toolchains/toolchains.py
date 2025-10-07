# Generic toolchain interface presented to the rest of the FVM framework. It
# imports different toolchain modules present in this same directory, which
# define the supported FVM methodology steps

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa', 'sby']
default_toolchain = 'questa'

def get_toolchain():
    """Get the toolchain from a specific environment variable. In the future,
    if the environment variable is not set, we plan to auto-detect which tools
    are available in the PATH and assign the first we find (with some
    priority)"""
    toolchain = os.getenv('FVM_TOOLCHAIN', default_toolchain)
    return toolchain

def get_default_flags(toolchain):
    """Returns sensible tool flags for a specific toolchain"""
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    default_flags = module.default_flags
    return default_flags

def define_steps(framework, steps, toolchain):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.define_steps(framework, steps)

def set_timeout(framework, toolchain, step, timeout):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_timeout(framework, step, timeout)

def set_coverage_goal(toolchain, step, goal):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_coverage_goal(step, goal)

def generics_to_args(toolchain, generics):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    return module.generics_to_args(generics)

def formal_initialize_reset(framework, toolchain, reset, active_high=True, cycles=1):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.formal_initialize_reset(framework, reset, active_high=active_high, cycles=cycles)

def get_linecheck_patterns(framework, step=None):
    """
    Import the corresponding toolchain module and call its
    get_linecheck_{step} function to obtain patterns.
    """
    if step is None:
        return {}

    module = importlib.import_module(f'fvm.toolchains.{framework.toolchain}')
    func_name = f"get_linecheck_{step.replace('.', '_')}"
    get_patterns_func = getattr(module, func_name, None)

    if get_patterns_func is None:
        return {}

    return get_patterns_func()
