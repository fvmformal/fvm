# Generic toolchain interface presented to the rest of the FVM framework. It
# imports different toolchain modules present in this same directory, which
# define the supported FVM methodology steps

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa', 'sby']
default_toolchain = 'questa'

default_flags = {}

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
    print(f'***** {module=}')
    print(f'***** {default_flags=}')
    return default_flags

def define_steps(steps, toolchain):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.define_steps(steps)

def set_timeout(framework, toolchain, step, timeout):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_timeout(framework, step, timeout)
