"""
Functions to traverse the dictionary and just print what they see.
Useful for debug, but they do not generate anything.
"""

# Allow writing to stderr
import sys

# Allow to compare data type to Dict
from typing import Dict

# Import our own constant definitions
from fvm.drom2psl.definitions import SIGNAL, EDGE, ASSIGN, CONFIG

def traverse(prefix, element):
    """
    Traverse a wavedrom element

    :param prefix: string to print before the element
    :type prefix: string
    :param element: element to traverse
    :type element: any

    :returns: None
    :rtype: None
    """
    print(prefix,  "traverse:", type(element), "=>", element)
    if isinstance(element, list):
        print(prefix, "is list:", element)
        traverse_list(prefix+"  ", element)
    elif isinstance(element, Dict):
        print(prefix, "is dict:", element)
        traverse_dict(prefix+"  ", element)
    else:
        print(prefix, "is other:", type(element), element)
        traverse_other(prefix+"  ", element)

def traverse_list(prefix, l):
    """
    Traverse a wavedrom list

    :param prefix: string to print before the list
    :type prefix: string
    :param l: list to traverse
    :type l: list

    :returns: None
    :rtype: None
    """
    print(prefix, "traverse_list:", type(l), "=>", l)
    for index, value in enumerate(l):
        print(prefix, "ele=>", index, "val=>", value)
        traverse(prefix+"  ", value)

def traverse_dict(prefix, d):
    """
    Traverse a wavedrom dict

    :param prefix: string to print before the dict
    :type prefix: string
    :param d: dictionary to traverse
    :type d: dict

    :returns: None
    :rtype: None
    """
    print(prefix, "traverse_dict:", type(d), "=>", d)
    for key, value in d.items():
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
    """
    Traverse a wavedrom element which is neither a list or a dict

    :param prefix: string to print before the element
    :type prefix: string
    :param other: element to traverse
    :type other: any

    :returns: None
    :rtype: None
    """
    print(prefix, "traverse_other:", type(other), other)

def traverse_signal(prefix, signal):
    """
    Traverse a wavedrom signal

    :param prefix: string to print before the signal
    :type prefix: string
    :param signal: signal to traverse
    :type signal: list

    :returns: None
    :rtype: None
    """
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
            print("ERROR:", prefix, "  element=>", index, "type=>", type(value),
                  "(unknown, should be either a wavelane or a group of wavelanes)")
            print(prefix, "signal element=>", index, "value=>", value)
            traverse(prefix+"  ", value)

def traverse_edge(prefix, edge):
    """
    Traverse a wavedrom edge

    :param prefix: string to print before the edge
    :type prefix: string
    :param edge: edge to traverse
    :type edge: list of strings

    :returns: None
    :rtype: None
    """
    print(prefix, "edge=>", edge)
