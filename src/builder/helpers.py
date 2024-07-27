# Helper functions
import inspect

def getscriptname():
    scriptname = inspect.stack()[-1][1]
    return(scriptname)
