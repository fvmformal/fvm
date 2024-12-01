# Helper functions
import inspect
import os
import sys
from humanize.time import precisedelta

def getscriptname():
    """Gets the absolute path of the called python script"""
    scriptname = os.path.abspath(sys.argv[0])
    return(scriptname)

def is_interactive():
    """Returns True if running from a python interpreter and False if running
    from a script"""
    return not hasattr(sys.modules['__main__'], '__file__')

def is_inside_venv():
    """Returns True if we are inside a venv, false if not"""
    if sys.prefix == sys.base_prefix:
        is_venv = True
    else:
        is_venv = False

    return is_venv

def readable_time(seconds):
    """Converts a time in seconds to the most appropriate unit"""
    if seconds <= 1:
        ret = "{:.2f}".format(seconds)+' seconds'
    else:
        ret = precisedelta(seconds)
    return ret
