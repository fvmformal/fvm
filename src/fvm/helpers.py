# Copyright 2024-2026 Universidad de Sevilla
# SPDX-License-Identifier: Apache-2.0

"""Helper functions for FVM"""
import os
import sys
from packaging.version import Version
from importlib.metadata import version as get_version

def get_fvm_version():
    """Returns the full version number (major.minor.patch[.others]) of the FVM"""
    versionstring = get_version("fvm-formal")
    return versionstring

def get_fvm_shortversion():
    """Returns the short version number (major.minor) of the FVM"""
    versionstring = get_version("fvm-formal")
    versionclass = Version(versionstring)
    ret = f'{versionclass.major}.{versionclass.minor}'
    return ret

def getscriptname():
    """Gets the absolute path of the called python script"""
    scriptname = os.path.abspath(sys.argv[0])
    return scriptname

def is_interactive():
    """Returns True if running from a python interpreter and False if running
    from a script"""
    return not hasattr(sys.modules['__main__'], '__file__')

def is_inside_venv():
    """Returns True if we are inside a venv, false if not"""
    return sys.prefix == sys.base_prefix

def readable_time(seconds):
    """Converts seconds into a readable format with up to 2 fields.
       Suppresses the second field if its value is zero.
       Uses singular or plural automatically.
    """

    def unit(value, singular, plural):
        return f"{value} {singular if value == 1 else plural}"

    if seconds < 1:
        return f"{seconds:.2f} seconds"

    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    if days > 0:
        if hours > 0:
            return f"{unit(days, 'day', 'days')}, {unit(hours, 'hour', 'hours')}"
        else:
            return unit(days, 'day', 'days')

    if hours > 0:
        if minutes > 0:
            return f"{unit(hours, 'hour', 'hours')}, {unit(minutes, 'minute', 'minutes')}"
        else:
            return unit(hours, 'hour', 'hours')

    if minutes > 0:
        if secs > 0:
            return f"{unit(minutes, 'minute', 'minutes')}, {unit(secs, 'second', 'seconds')}"
        else:
            return unit(minutes, 'minute', 'minutes')

    return unit(secs, 'second', 'seconds')

def insert_line_before_target(file, target_line, line_to_insert):
    """Inserts a line before the first occurrence of target_line in file"""
    with open(file, 'r', encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip() == target_line:
            new_lines.append(line_to_insert + '\n')
        new_lines.append(line)

    with open(file, 'w', encoding="utf-8") as f:
        f.writelines(new_lines)

def insert_line_after_target(file, target_line, line_to_insert):
    """Inserts a line after the first occurrence of target_line in file"""
    with open(file, 'r', encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip() == target_line:
            new_lines.append(line_to_insert + '\n')

    with open(file, 'w', encoding="utf-8") as f:
        f.writelines(new_lines)
