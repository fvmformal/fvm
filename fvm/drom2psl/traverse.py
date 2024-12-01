# Import our own constant definitions
from fvm.drom2psl.definitions import *

# Allow to compare data type to Dict
from typing import Dict

"""
Functions to traverse the dictionary and just print what they see
Useful for debug, but they do not generate anything
"""

def traverse(prefix, value):
    print(prefix,  "traverse:", type(value), "=>", value)
    if isinstance(value, list):
        print(prefix, "is list:", value)
        traverse_list(prefix+"  ", value)
    elif isinstance(value, Dict):
        print(prefix, "is dict:", value)
        traverse_dict(prefix+"  ", value)
    else:
        print(prefix, "is other:", type(value), value)
        traverse_other(prefix+"  ", value)

def traverse_list(prefix, list):
    print(prefix, "traverse_list:", type(list), "=>", list)
    for index, value in enumerate(list):
        print(prefix, "ele=>", index, "val=>", value)
        traverse(prefix+"  ", value)

def traverse_dict(prefix, dict):
    print(prefix, "traverse_dict:", type(dict), "=>", dict)
    for key, value in dict.items():
        print(prefix, "type(key:)", type(key), "=>", "type(value:)", type(value))
        #print(prefix, "key=>", key, "val=>", value)
        if key == SIGNAL:
            print(prefix, "is signal")
            traverse_signal(prefix+"  ", value)
        elif key == EDGE:
            print(prefix, "is edge")
            traverse_edge(prefix+"  ", value)
        elif key == ASSIGN:
            print(prefix, "is assign")
            traverse_edge(prefix+"  ", value)
        elif key == CONFIG:
            print(prefix, "is config")
            traverse_edge(prefix+"  ", value)
        else:
            print(prefix, "is other")
            traverse(prefix+"  ", value)

def traverse_other(prefix, other):
    print(prefix, "traverse_other:", type(other), other)
    pass

def traverse_signal(prefix, signal):
    # Signal must be a list
    if not isinstance(signal, list):
        print("ERROR: signal must be a list", file=sys.stderr)
    # Here we check for groups
    #   a normal signal is list of dicts with name, wave
    #   a group is a list whose first value is a string and not a dict
    print(prefix, "signal=>", signal)
    for index, value in enumerate(signal):
        if isinstance(value, Dict):
            print(prefix, "signal element=>", index, "type=>", type(value), "(wavelane)")
            traverse(prefix+"  ", value)
        elif isinstance(value, list):
            print(prefix, "signal element=>", index, "type=>", type(value), "(group of wavelanes)")
            for i in value:
                traverse(prefix+"  ", i)
        else:
            print("ERROR:", prefix, "  element=>", index, "type=>", type(value), "(unknown, should be either a wavelane or a group of wavelanes)")
            print(prefix, "signal element=>", index, "value=>", value)
            traverse(prefix+"  ", value)

def traverse_edge(prefix, edge):
    print(prefix, "edge=>", edge)

