# Toolchain definitions file

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa']
default_toolchain = 'questa'

TOOLS = {}
default_flags = {}

# Programmatically import all toolchains and get the constants defined in each
# of them
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

