"""
Functions to actually interpret the wavedrom dictionary
"""

# To allow pretty cool debug prints than can be disabled after development
# Explanation at: https://towardsdatascience.com/do-not-use-print-for-debugging-in-python-anymore-6767b6f1866d
from icecream import ic

#if DEBUG == False:
#    ic.disable

# Allow to compare data type to Dict
from typing import Dict

# Import our own constant definitions
from fvm.drom2psl.definitions import *

# Allow printing to sys.stderr
import sys

# Import our own logging functions
from fvm.drom2psl.logging import *

"""
Get signal field from dict
"""
def get_signal(dictionary):
    #ic(type(dictionary))
    #ic(dictionary)
    #for key, value in dictionary.items():
    #    ic(key,, value)
    assert isinstance(dictionary, Dict), "dictionary should be an actual python Dict"
    if SIGNAL in dictionary:
        signal_list = dictionary.get(SIGNAL)
        ok = True
    else:
        error("No 'signal' list found in input file")
        signal_list = None
        ok = False
    return signal_list, ok

"""
List elements in signal field
"""
def list_signal_elements(signal):
    ic(type(signal))
    assert isinstance(signal, list), "wavelanes should be a list"
    for index, value in enumerate(signal):
        if isinstance(value, Dict):
            print(prefix, "signal element=>", index, "type=>", type(value), "(wavelane)")
        elif isinstance(value, list):
            print(prefix, "signal element=>", index, "type=>", type(value), "(group of wavelanes)")
        else:
            error(str(prefix)+"   element=> "+str(index)+" type=> "+str(type(value))+" (unknown, should be either a wavelane or a group of wavelanes)")

"""
Check wavelane for correctness.

In normal wavedrom, a wavelane is always correct if it is a dictionary. It can
be empty, but it can also have 'name', 'wave', 'data' or 'node' fields.

We'll be a bit more restrictive:
    - We will allow (and ignore) empty wavelanes
    - If a wavelane is not empty, it needs to have at least a 'name' field
    - For now we will allow not having a 'wave' field, but probably we will
      need to check for that too, because having empty waves or no waves
      doesn't make sense
"""
def check_wavelane(wavelane):
    #ic(wavelane)
    status = True
    if len(wavelane) == 0:
        ic("wavelane is empty, but this is no problem")
    else:
        #ic(NAME in wavelane, WAVE in wavelane, DATA in wavelane, NODE in wavelane)
        #ic(NAME in wavelane, WAVE in wavelane)
        #ic(DATA in wavelane, NODE in wavelane)
        #print(wavelane)
        if NAME not in wavelane:
            error("wavelane "+str(wavelane)+" has no 'name' field. Check that the key 'name' exists and there is at least a space after the colon (:)")
            status = False
        if WAVE not in wavelane:
            warning("wavelane"+str(wavelane)+"has no 'wave' field.")
    return status

"""
Check if wavelane is empty.
"""
def is_empty(wavelane):
    if len(wavelane) == 0:
        return True
    else:
        return False

"""
Get the type of a signal element

A wavelane is a dictionary
A group of wavelanes is a list
"""
def get_type(element):
    if isinstance(element, Dict):
        ret = WAVELANE
    elif isinstance(element, list):
        ret = GROUP
    elif isinstance(element, str):
        ret = STRING
    else:
        error("element=>", element, "type=>", type(element), "(unknown, should be either a wavelane (dict) or a group of wavelanes (list))")
        ret = "others"
    return ret

"""
List all signal elements
"""
def list_elements(prefix, signal):
    for index, value in enumerate(signal):
        elementtype = get_type(value)
        print(prefix, "INFO:  element=>", index, "type=>", elementtype, "value=>", value)
        # List groups recursively (we'll use this to flatten the groups)
        if elementtype == GROUP:
            print(prefix, "is group!")
            list_elements(prefix+"  ", value)

"""
Get name of group.

The name of the group is the first element of the list, which should be a
string
"""
def get_group_name(group):
    #ic(type(group))
    #ic(group)
    assert isinstance(group, list), "group should be a list"
    assert isinstance(group[0], str), "group[0] should be a str"
    return group[0]

"""
Flatten the signal field.

We do this by generating a new list of signalelements where there are no
groups: instead, groups/subgroup names are added as prefixes to the name field
of each wavelane that is inside a group

For each signalelement:
    if it is a signal, just append it to the flattened list
      to do that, first copy the original wavelane
      and then append the current group name to the wavelane's name field
    if it is a group, flatten it recursively: set the group name as the new
      prefix and call flatten passing it the rest of the element
    if it is a string, something is wrong (strings should be only the names of
      the groups, and we should have caught that when operating with the group)
"""
def flatten (group, signal, flattened=None, hierarchyseparator="."):

    # ok == True is correct, ok == False means some error was found
    ok = True

    # Create a list if no list was provided
    if flattened is None:
        flattened = []

    # Do not include separator in the top-level of the hierarchy
    if group == "":
        separator = ""
    else:
        separator = hierarchyseparator

    #ic(group)
    for i, value in enumerate(signal):
        # Stop processing if there are any errors
        if not ok :
            break

        # If a wavelane, append it to the flattened list
        if get_type(value) == WAVELANE:
            wavelane = signal[i].copy()
            if not is_empty(wavelane):
                ok = check_wavelane(wavelane)
                if ok :
                    wavelane[NAME] = group + separator + signal[i].get(NAME)
                    flattened.append(wavelane)

        # If a group, recursively flatten its members
        elif get_type(value) == GROUP:
            #ic(signal[i][0])
            flattened, ok = flatten(group + separator + signal[i][0], signal[i][1:], flattened, hierarchyseparator)

        # If something unexpected, signal an error
        else: #if get_type(value) == signalelements.STRING.value:
            error(group, i, "is unexpected type", get_type(value), "of", value)
            ok = False

    return flattened, ok

