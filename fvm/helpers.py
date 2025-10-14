"""Helper functions for FVM"""
# Helper functions
import os
import sys

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
        return f"{seconds:.2f} seconds"

    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days} days,")
    if hours:
        parts.append(f"{hours} hours,")
    if minutes:
        parts.append(f"{minutes} minutes,")
    if secs or not parts:
        parts.append(f"{secs} seconds")

    return " ".join(parts)

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
