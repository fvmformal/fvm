"""
Functions to actually interpret the wavedrom dictionary
"""

# Allow usage of regular expressions
import re

# Allow to compare data type to Dict
from typing import Dict

# To allow pretty cool debug prints than can be disabled after development
from icecream import ic

# Import our own constant definitions
from fvm.drom2psl.definitions import (SIGNAL, WAVELANE, GROUP, STRING, NAME,
                                      WAVE, DATA, TYPE)

# Import our own logging functions
from fvm.drom2psl.basiclogging import warning, error

def get_signal(dictionary):
    """
    Get signal field from dictionary

    :param dictionary: wavedrom dictionary
    :type dictionary: dict

    :returns: a (signal_list, ok) tuple. signal_list is the signal field, ok is
              True if there were no errors, False if there were any
    :type: (list, bool)
    """
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

def list_signal_elements(prefix, signal):
    """
    List elements in signal field

    :param prefix: prefix for printing debugging messages
    :type prefix: str
    :param signal: signal field
    :type signal: list

    :returns: None
    :rtype: None
    """
    ic(type(signal))
    assert isinstance(signal, list), "wavelanes should be a list"
    for index, value in enumerate(signal):
        if isinstance(value, Dict):
            print(prefix, "signal element=>", index, "type=>", type(value), "(wavelane)")
        elif isinstance(value, list):
            print(prefix, "signal element=>", index, "type=>", type(value), "(group of wavelanes)")
        else:
            error(str(prefix)+"   element=> "+str(index)+" type=> "
                  +str(type(value))+
                  " (unknown, should be either a wavelane or a group of wavelanes)")

def check_wavelane(wavelane):
    """
    Check wavelane for correctness.

    In normal wavedrom, a wavelane is always correct if it is a dictionary. It can
    be empty, but it can also have 'name', 'wave', 'data' or 'node' fields.

    We'll be a bit more restrictive:
        - We will allow (and ignore) empty wavelanes
        - If a wavelane is not empty, it needs to have at least a 'name' field
        - For now we will allow not having a 'wave' field, but probably we will
          need to check for that too, because having empty waves or no waves
          doesn't make much sense

    :param wavelane: wavelane to analyze
    :type wavelane: dict

    :returns: True if ok, False if there are any errors
    :rtype: bool
    """
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
            error("wavelane "+str(wavelane)+
                  (" has no 'name' field. Check that the key 'name' exists and"
                   " there is at least a space after the colon (:)"))
            status = False
        if WAVE not in wavelane:
            warning("wavelane"+str(wavelane)+"has no 'wave' field.")
    return status

def is_empty(wavelane):
    """
    Check if wavelane is empty.

    :param wavelane: wavelane to check
    :type wavelane: dict

    :returns: True if empty, False if not empty
    :rtype: bool
    """
    return bool(len(wavelane) == 0)

def get_type(element):
    """
    Get the type of a signal element.

    - A wavelane is a dictionary
    - A group of wavelanes is a list

    :param element: signal element to analyze
    :type element: dict or list

    :returns: one of the following: WAVELANE, GROUP, STRING, "others"
    :rtype: str
    """
    if isinstance(element, Dict):
        ret = WAVELANE
    elif isinstance(element, list):
        ret = GROUP
    elif isinstance(element, str):
        ret = STRING
    else:
        error("element=>", element, "type=>", type(element),
              "(unknown, should be either a wavelane (dict) or a group of wavelanes (list))")
        ret = "others"
    return ret

def list_elements(prefix, signal):
    """
    List all elements in a signal

    :param prefix: prefix for printing debugging messages
    :type prefix: str
    :param signal: signal to list
    :type signal: list

    :returns: None
    :rtype: None
    """
    for index, value in enumerate(signal):
        elementtype = get_type(value)
        print(prefix, "INFO:  element=>", index, "type=>", elementtype, "value=>", value)
        # List groups recursively (we'll use this to flatten the groups)
        if elementtype == GROUP:
            print(prefix, "is group!")
            list_elements(prefix+"  ", value)

def get_group_name(group):
    """
    Get name of group.

    The name of the group is the first element of the list, which should be a
    string

    :param group: group from which to get the name
    :type group: list

    :returns: the group name
    :rtype: str
    """
    #ic(type(group))
    #ic(group)
    assert isinstance(group, list), "group should be a list"
    assert isinstance(group[0], str), "group[0] should be a str"
    return group[0]

def flatten (group, signal, flattened=None, hierarchyseparator="."):
    """
    Flatten the signal field.
    
    We do this by generating a new list of signalelements where there are no
    groups: instead, groups/subgroup names are added as prefixes to the name field
    of each wavelane that is inside a group
    
    For each signalelement:
        - if it is a signal, just append it to the flattened list
          - to do that, first copy the original wavelane
          - and then append the current group name to the wavelane's name field
        - if it is a group, flatten it recursively: set the group name as the new
          prefix and call flatten passing it the rest of the element
        - if it is a string, something is wrong (strings should be only the names of
          the groups, and we should have caught that when operating with the group)

    :param group: group prefix from which the signal descends
    :type group: str
    :param signal: signal to flatten
    :type signal: list
    :param flattened: already flattened signal (for recursive flattening groups)
    :type flattened: list or None
    :param hierarchyseparator: hierarchy separator for the flattened
                               representation
    :type hierarchyseparator: str

    :returns: a (flattened, ok) tuple. flattened is the flattened signal, ok is
              True if there were no errors, False if there were any
    :type: (list, bool)
    """
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
            flattened, ok = flatten(group + separator + signal[i][0],
                                    signal[i][1:], flattened,
                                    hierarchyseparator)

        # If something unexpected, signal an error
        else: #if get_type(value) == signalelements.STRING.value:
            error(group, i, "is unexpected type", get_type(value), "of", value)
            ok = False

    return flattened, ok

def get_wavelane_name(wavelane):
    """Get the `name` field of a wavelane

    :param wavelane: wavelane whose name we want to get
    :type wavelane: dict

    :return: name of the wavelane
    :rtype: string
    """
    return wavelane[NAME]

def get_wavelane_wave(wavelane):
    """Get the `wave` field of a wavelane

    :param wavelane: wavelane whose wave we want to get
    :type wavelane: dict

    :return: wave field of the wavelane
    :rtype: string
    """
    return wavelane[WAVE]

def get_wavelane_data(wavelane):
    """Get the `data` field of a wavelane, if it exists

    :param wavelane: wavelane whose data we want to get
    :type wavelane: dict

    :return: data field of the wavelane
    :rtype: can be list or a string, use data2list to ensure it is a list
    """
    if DATA in wavelane:
        return wavelane[DATA]
    return None

def get_wavelane_type(wavelane):
    """Get the `type` field of a wavelane, if it exists

    :param wavelane: wavelane whose type we want to get
    :type wavelane: dict

    :return: type field of the wavelane
    :rtype: string
    """
    if TYPE in wavelane:
        ret = wavelane[TYPE]
    else:
        warning(f"""data field present in {wavelane=} but no datatype
        specified. If a datatype is specified, it will be included in the
        generated PSL file, for example: type: 'std_ulogic_vector(31 downto 0)'
                """)
        ret = "specify_datatype_here"
    return ret

def get_group_arguments(groupname, flattened_signal):
    """Get the arguments of a group

    A group is a set of wavelanes which are grouped together in the .json, and
    its arguments are all values in the `data` field of its wavelanes that are
    not literal values. For example if a wavelane inside a group has a data
    field that is ``[0, 127, addr, 42]`` then ``addr`` is an argument for the
    group.

    :param groupname: name of the group
    :type groupname: string
    :param flattened_signal: a flattened signal
    :type flattened_signal: string

    :returns: a list of arguments for the group
    :rtype: list
    """
    group_arguments = []
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
                deduplicated_data = list(dict.fromkeys(non_paren_data))
                ic(deduplicated_data)
                data_after_exclusion = exclude_data_types(deduplicated_data)
                # Create a new list with each argument and its datatype
                args_with_type = [[d, datatype] for d in data_after_exclusion]
                ic(args_with_type)
                group_arguments.extend(args_with_type)
    return group_arguments

def exclude_data_types(datalist):
    """Exclude VHDL types from a data list"""
    new_datalist = []
    for data in datalist:
        if isinstance(data, int):
            pass
        elif data.startswith("0x"):
            pass
        elif re.match(r'^[01]+$', data):
            pass
        else:
            new_datalist.append(data)

    return new_datalist

def remove_parentheses(string):
    """Removes anything between parentheses, including the parentheses, from a
    string"""
    if isinstance(string, int):
        return string
    return re.sub(r'\([^)]*\)', '', string).strip()

def data2list(wavelane_data):
    """Converts wavelane data to a list if it is a string, returns it untouched
    if it is already a list"""
    if isinstance(wavelane_data, str):
        ret = wavelane_data.split()
    else:
        ret = wavelane_data
    return ret

def get_clock_value(wavelane, cycle):
    """
    Get the value of the clock during a specific cycle of the wavelane. This
    value is not an electronic signal value (such as zero, one, rising_edge,
    etc) but a binary coded value that tells us if that cycle is to be repeated
    or not:

    - ``1``: Do once
    - ``0``: Repeat zero or more times

    :param wavelane: wavelane of the clock signal
    :type wavelane: dict
    :param cycle: clock cycle
    :type cycle: integer

    :returns: clock repeat value (``0`` or ``1``)
    :rtype: int
    """
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
    pipe = bool(digit == '|')
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

def get_signal_value(wave, data, cycle):
    """Get value of signal at a specific clock cycle"""
    datadigits = ['=', '2', '3', '4', '5', '6', '7', '8', '9']
    digit = wave[cycle]
    ic(data, type(data))
    if data is not None:
        datalist = data2list(data)
    else:
        datalist = []

    if digit in ['p', 'P', 'n', 'N']:
        value = '-'
        warning(f'{value=} not an appropriate value for a non-clock signal, ignoring')
    elif digit in ['<', '>']:
        value = '-'
        error("Stretching/widening operators > and < not supported")
    elif digit in ['.', '|'] and cycle == 0:
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
    elif digit in ['0', 'l', 'L']:
        value = '0'
    elif digit in ['1', 'h', 'H']:
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
        # Here differentiate between integer, binary, hex, and argument,
        if position < len(data):
            if isinstance(datalist[position], int):
                value = (datalist[position], "int")
            elif datalist[position].startswith("0x"):
                value = (datalist[position], "hex")
            elif re.match(r'^[01]+$', datalist[position]):
                value = (datalist[position], "bin")
            else:
                value = (datalist[position], "arg")
        else:
            value = '-'
    else:
        warning(f"Unrecognized {digit=}, will treat as don't care")
        value = '-'

    return value

def adapt_value_to_hdltype(value):
    """
    Adds the necessary characters (such as simple or double quotes, ``0x``,
    etc) to convert a literal value to a properly formated VHDL datatype

    The input value can be either a single character with a valid
    ``std_ulogic`` value, or `(value, type)` tuple where `type` is one of
    the following:

    - ``"bin"`` (binary)
    - ``"hex"`` (hexadecimal)
    - ``"int"`` (integer)
    - ``"arg"`` (argument)

    :param value: value to convert
    :type value: single-char str or tuple

    :returns: adapted value
    :rtype: str
    """
    # For std_logic, just add a couple of single quotes to the character
    if value in ['0', '1', 'L', 'H', 'W', 'X', 'Z', 'U', '-']:
        ret = "'"+value+"'"
    # binary
    elif isinstance(value, tuple) and len(value) > 1 and value[1] == "bin":
        ret = f'"{value[0]}"'
    # hexadecimal
    elif isinstance(value, tuple) and len(value) > 1 and value[1] == "hex":
        ret = f'x"{value[0][2:]}"'
    # integer
    elif isinstance(value, tuple) and len(value) > 1 and value[1] == "int":
        ret = f'{value[0]}'
    # Any other values (such as those specified in the 'data' fields) are
    # returned without modification
    elif isinstance(value, tuple) and len(value) > 1 and value[1] == "arg":
        ret = f'{value[0]}'
    else:
        ret = value
    return ret
