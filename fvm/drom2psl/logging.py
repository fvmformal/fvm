"""
Quick and dirty logger using termcolor
"""

# Allow writing to stderr
import sys

# Allow color printing for INFO, WARNING and ERROR messages which will be
# generated with print (and thus will remain even when we disable icecream)
from termcolor import colored

# Let's wrap the print function to have info(), warning() and error()
# We do this by mixing two answers from this stackoverflow link: https://stackoverflow.com/questions/26286203/custom-print-function-that-wraps-print
#   Prepending characters: https://stackoverflow.com/a/26286813
#   Passing both arguments and keyword arguments (kwargs): https://stackoverflow.com/a/64885453

"""
Print INFO message (to stdout)
"""
def info(*args, **kwargs):
    args = (colored("INFO:", 'blue'),) + args
    print(*args, **kwargs)

"""
Print WARNING message (to stderr)
"""
def warning(*args, **kwargs):
    args = (colored("WARNING:", 'yellow'),) + args
    print(*args, file=sys.stderr, **kwargs)

"""
Print ERROR message (to stderr)
"""
def error(*args, **kwargs):
    args = (colored("ERROR:", 'red'),) + args
    print(*args, file=sys.stderr, **kwargs)


