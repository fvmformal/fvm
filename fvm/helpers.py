# Helper functions
import os
import sys
from humanize.time import precisedelta

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
    """Converts a time in seconds to the most appropriate unit"""
    if seconds <= 1:
        ret = f"{seconds:.2f} seconds"
    else:
        ret = precisedelta(seconds)
    return ret

def insert_line_before_target(file, target_line, line_to_insert):
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
    with open(file, 'r', encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip() == target_line:
            new_lines.append(line_to_insert + '\n')

    with open(file, 'w', encoding="utf-8") as f:
        f.writelines(new_lines)
