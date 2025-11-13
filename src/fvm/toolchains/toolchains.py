"""Toolchain interface for FVM"""
# Generic toolchain interface presented to the rest of the FVM framework. It
# imports different toolchain modules present in this same directory, which
# define the supported FVM methodology steps

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa', 'sby']
DEFAULT_TOOLCHAIN = 'questa'

def get_toolchain():
    """
    Get the toolchain from a specific environment variable. If the environment
    variable is not set, the value of DEFAULT_TOOLCHAIN is returned.

    In the future, if the environment variable is not set, we plan to
    auto-detect which tools are available in the PATH and assign the first we
    find (with some priority)

    :return: toolchain name
    :rtype: str
    """
    toolchain = os.getenv('FVM_TOOLCHAIN', DEFAULT_TOOLCHAIN)
    return toolchain

def get_default_flags(toolchain):
    """
    Returns tool flags for a specific toolchain

    :param toolchain: toolchain name
    :type toolchain: str

    :return: list of default flags
    :rtype: list
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    default_flags = module.default_flags
    return default_flags

def define_steps(framework, steps, toolchain):
    """
    Import the corresponding toolchain module and call its define_steps function
    to define the steps in the framework.

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param steps: the Steps object where the steps will be registered
    :type steps: fvm.steps.Steps
    :param toolchain: toolchain name
    :type toolchain: str
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.define_steps(framework, steps)

def set_timeout(framework, toolchain, step, timeout):
    """
    Import the corresponding toolchain module and call its set_timeout function
    to set the timeout for a specific step.

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param toolchain: toolchain name
    :type toolchain: str
    :param step: step name
    :type step: str
    :param timeout: timeout
    :type timeout: str
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_timeout(framework, step, timeout)

def set_coverage_goal(toolchain, step, goal):
    """
    Import the corresponding toolchain module and call its set_coverage_goal function
    to set the coverage goal for a specific step.

    :param toolchain: toolchain name
    :type toolchain: str
    :param step: step name
    :type step: str
    :param goal: coverage goal
    :type goal: int or float
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_coverage_goal(step, goal)

def generics_to_args(toolchain, generics):
    """
    Import the corresponding toolchain module and call its generics_to_args
    function to convert generics to command line arguments.

    :param toolchain: toolchain name
    :type toolchain: str
    :param generics: dictionary of generics
    :type generics: dict
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    return module.generics_to_args(generics)

def formal_initialize_reset(framework, toolchain, reset, active_high=True, cycles=1):
    """
    Import the corresponding toolchain module and call its formal_initialize_reset
    function to initialize the design with a reset sequence.

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param toolchain: toolchain name
    :type toolchain: str
    :param reset: reset signal name
    :type reset: str
    :param active_high: True if the reset is active high, False if active low. Defaults to True
    :type active_high: bool
    :param cycles: number of cycles to hold the reset
    :type cycles: int
    """
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.formal_initialize_reset(framework, reset, active_high=active_high, cycles=cycles)

def get_linecheck_patterns(framework, step=None):
    """
    Import the corresponding toolchain module and call its
    get_linecheck_{step} function to obtain patterns.

    :param framework: the FvmFramework object
    :type framework: fvm.framework.FvmFramework
    :param step: step name (optional)
    :type step: str or None
    """
    if step is None:
        return {}

    module = importlib.import_module(f'fvm.toolchains.{framework.toolchain}')
    func_name = f"get_linecheck_{step.replace('.', '_')}"
    get_patterns_func = getattr(module, func_name, None)

    if get_patterns_func is None:
        return {}

    return get_patterns_func()
