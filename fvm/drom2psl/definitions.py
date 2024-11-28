"""
The json file must contain a dict

The dict described in the json file can have the following fields:
    signal (mandatory)
    edge   (optional)
    head   (optional)
    foot   (optional)
    assign (not supported, it is for drawing schematics)
    config (not supported, it is just for cosmetic purposes)
"""
SIGNAL   = "signal"
EDGE     = "edge"
HEAD     = "head"
FOOT     = "foot"
ASSIGN   = "assign"
CONFIG   = "config"

"""
signal is a list of signalelements

signalelements may be either dict or list
  if dict, signalelement is a wavelane
  if list, signalelement is a group of wavelanes

a group is a list that has:
  a name as first element (mandatory)
    and either:
  one or more groups
    or
  one or more wavelanes


"""
WAVELANE = "wavelane"
GROUP    = "group"
STRING   = "string"

"""
a wavelane may:
  be an empty wavelane
    or
  have at least a name field
  wave, data, node are optional
  period and phase are also optional (and currently not supported)
    period should be an integer. fractionary periods are ceil()'d up internally
      (i.e. 2.9 becomes 3)
    phase doesn't seem to have restrictions
"""
NAME     = "name"
WAVE     = "wave"
DATA     = "data"
NODE     = "node"
PERIOD   = "period"
PHASE    = "phase"

"""
an edge is a list of strings

each string has these tokens:
    <source><arrow><destination>[<whitespace><label>]

  source must have been defined in a node inside a wavelane
  destination must have been defined in a node inside a wavelane
  arrow must be one of the allowable values
  whitespace (optional) is just whitespace
  label (optional) can be any string

if a label is used, whitespace is mandatory
"""
SPLINE0 = "~"
SPLINE1 = "-~"
SPLINE2 = "<~>"
SPLINE3 = "<-~>"
SPLINE4 = "~>"
SPLINE5 = "-~>"
SPLINE6 = "~->"
SHARP0  = "-"
SHARP1  = "-|"
SHARP2  = "-|-"
SHARP3  = "<->"
SHARP4  = "<-|>"
SHARP5  = "<-|->"
SHARP6  = "->"
SHARP7  = "-|>"
SHARP8  = "-|->"
SHARP9  = "|->"
SHARP10 = "+"

