# Generic toolchain interface presented to the rest of the FVM framework. It
# imports different toolchain modules present in this same directory, which
# define the supported FVM methodology steps

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa', 'sby']
default_toolchain = 'questa'

# TODO : not sure we actually need TOOLS
TOOLS = {}
default_flags = {}

# Programmatically import all toolchains and get the constants defined in each
# of them
# TODO : not sure we actually need TOOLS
# TODO : since we probably won't need TOOLS, let's just import the specific
# module in get_default_flags, as we do in define_steps
for t in toolchains:
    module = importlib.import_module(f'fvm.toolchains.{t}')
    default_flags[t] = module.default_flags
    TOOLS[t] = module.tools

def get_toolchain():
    """Get the toolchain from a specific environment variable. In the future,
    if the environment variable is not set, we plan to auto-detect which tools
    are available in the PATH and assign the first we find (with some
    priority)"""
    toolchain = os.getenv('FVM_TOOLCHAIN', default_toolchain)
    return toolchain

def get_default_flags(toolchain):
    print(f'get_default_flags: {toolchain=}')
    print(f'get_default_flags: {default_flags=}')
    print(f'get_default_flags: {default_flags[toolchain]=}')
    print(f'get_default_flags: {default_flags.get(toolchain)=}')
    return default_flags.get(toolchain)

def define_steps(steps, toolchain):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.define_steps(steps)

