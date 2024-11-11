# Helper functions
import inspect
from humanize.time import precisedelta

def getscriptname():
    scriptname = inspect.stack()[-1][1]
    return(scriptname)

def readable_time(seconds):
    if seconds <= 1:
        ret = "{:.2f}".format(seconds)
    else:
        ret = precisedelta(seconds)
    return ret
