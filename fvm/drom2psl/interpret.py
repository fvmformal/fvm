"""
Functions to actually interpret the wavedrom dictionary
"""

# To allow pretty cool debug prints than can be disabled after development
# Explanation at: https://towardsdatascience.com/do-not-use-print-for-debugging-in-python-anymore-6767b6f1866d
from icecream import ic

# Allow usage of regular expressions
import re

# Allow to have ordered dicts (used to preserve order when removing duplicated
# arguments)
from collections import OrderedDict

#if DEBUG == False:
#    ic.disable

# Allow to compare data type to Dict
from typing import Dict

# Import our own constant definitions
from fvm.drom2psl.definitions import *

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
def list_signal_elements(prefix, signal):
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

def get_wavelane_name(wavelane):
    return wavelane[NAME]

def get_wavelane_wave(wavelane):
    return wavelane[WAVE]

def get_wavelane_data(wavelane):
    if DATA in wavelane:
        return wavelane[DATA]
    else:
        return None

def get_wavelane_type(wavelane):
    if TYPE in wavelane:
        return wavelane[TYPE]
    else:
        warning(f"""data field present in {wavelane=} but no datatype
        specified.  If a datatype is specified, it will be included in the
        generated PSL file, for example: type: 'std_ulogic_vector(31 downto 0)'
                """)
        return "specify_datatype_here"

def get_group_arguments(groupname, flattened_signal):
    group_arguments = list()
    for wavelane in flattened_signal:
        name = get_wavelane_name(wavelane)
        # If the wavelane belongs to a group
        if name[:len(groupname)] == groupname:
            # Get the data field
            data = get_wavelane_data(wavelane)
            if data is not None:
                ic(data, type(data))
                # Get the datatype
                datatype = get_wavelane_type(wavelane)
                # Get the data
                actualdata = data2list(data)
                ic(actualdata)
                # Remove anything between parentheses: we don't want data(0)
                # and data(1) to be different arguments
                non_paren_data = [remove_parentheses(d) for d in actualdata]
                ic(non_paren_data)
                # Remove duplicated arguments without losing ordering
                deduplicated_data = unique_list = list(dict.fromkeys(non_paren_data))
                ic(deduplicated_data)
                # Create a new list with each argument and its datatype
                args_with_type = [[d, datatype] for d in deduplicated_data]
                ic(args_with_type)
                group_arguments.extend(args_with_type)
    return group_arguments

def remove_parentheses(string):
    """Removes anything between parentheses, including the parentheses, from a
    string"""
    return re.sub(r'\([^)]*\)', '', string).strip()

def data2list(wavelane_data):
    """Converts wavelane data to a list if it is a string, returns it untouched
    if it is already a list"""
    if type(wavelane_data) == str:
        return wavelane_data.split()
    else:
        return wavelane_data

def get_clock_value(wavelane, cycle):
    wave = get_wavelane_wave(wavelane)
    digit = wave[cycle]
    clkdigits = ['p', 'P', 'n', 'N', '.', '|']

    if digit not in clkdigits:
        warning(f'{digit=} not an appropriate value for a clock signal')
        value = 1  # Do once
    elif digit == '|':
        value = 0  # Repeat zero or more
    else:
        value = 1  # Do once

    return value

def is_pipe(wavelane, cycle):
    """Returns True if the 'data' at 'cycle' in 'wave' is a pipe (|), which
    means: 'repeat zero or more times'"""
    wave = get_wavelane_wave(wavelane)
    digit = wave[cycle]
    if digit == '|':
        pipe = True
    else:
        pipe = False
    return pipe

def gen_sere_repetition(num_cycles, or_more, add_semicolon = False, comments = True):
    """Generates the SERE repetition operator according to the number of cycles
    received and if N 'or more' cycles can be matched"""
    if or_more is False:
        text = f'[*{num_cycles}]'  # Exactly num_cycles
        if add_semicolon:
            text += ';'
        if comments:
            text += f'  -- {num_cycles} cycle'
            if num_cycles != 1:
                text += 's'
    elif or_more is True:
        if num_cycles == 0:
            text = '[*]'  # Zero or more
            if add_semicolon:
                text += ';'
            if comments:
                text += '  -- 0 or more cycles'
        elif num_cycles == 1:
            text = '[+]'  # One or more. Could also be [*1:inf]
            if add_semicolon:
                text += ';'
            if comments:
                text += '  -- 1 or more cycles'
        else:
            text = f'[*{num_cycles}:inf]'  # N or more
            if add_semicolon:
                text += ';'
            if comments:
                text += f'  -- {num_cycles} or more cycles'
    return text

# TODO : assignments could be tailored to the datatypes
def get_signal_value(wave, data, cycle):
    datadigits = ['=', '2', '3', '4', '5', '6', '7', '8', '9']
    digit = wave[cycle]
    ic(data, type(data))
    if data is not None:
        datalist = data2list(data)
    else:
        datalist = list()

    if digit == 'p' or digit == 'P' or digit == 'n' or digit == 'N':
        value = '-'
        warning(f'{value=} not an appropriate value for a non-clock signal, ignoring')
    elif digit == '<' or digit == '>':
        value = '-'
        error("Stretching/widening operators > and < not supported")
    elif (digit == '.' or digit == '|') and cycle == 0:
        error("""Cannot repeat previous value if there is no previous
        value: '.' and '|' are not supported on the first clock cycle""")
    elif digit == '.':
        value = get_signal_value(wave, data, cycle-1)
    elif digit == '|':
        value = get_signal_value(wave, data, cycle-1)
    elif digit == 'd':
        value = '0'
    elif digit == 'u':
        value = '1'
    elif digit == 'z':
        value = 'Z'
    elif digit == 'x':
        value = '-'
    elif digit == '0' or digit == 'l' or digit == 'L':
        value = '0'
    elif digit == '1' or digit == 'h' or digit == 'H' :
        value = '1'
    elif digit in datadigits:

        # Initialize a pointer to the data list
        position = 0

        # For each time a data has been used before, advance the pointer to the
        # data list
        for c in range(cycle):
            cycledigit = wave[c]
            if cycledigit in datadigits:
                position += 1

        # When we reach the current cycle, if the pointer is inside the data
        # list, there is a data for us to use. If the pointer is outside, then
        # we don't have anything to compare to so we'll consider it a don't
        # care
        if position < len(data):
            value = datalist[position]
        else:
            value = '-'
    else:
        warning(f"Unrecognized {digit=}, will treat as don't care")
        value = '-'

    return value

# TODO : here we are converting 0/1/etc to std_ulogic '0'/'1'/etc, but in the
# future we could receive the hdltype as argument, to support different
# datatypes, such as integer
def adapt_value_to_hdltype(value):
    # For std_logic, just add a couple of single quotes to the character
    if value in ['0', '1', 'L', 'H', 'W', 'X', 'Z', 'U', '-']:
        ret = "'"+value+"'"
    # Any other values (such as those specified in the 'data' fields) are
    # returned without modification
    else:
        ret = value
    return ret

