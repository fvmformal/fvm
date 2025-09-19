"""
The json file must contain a dict

The dict described in the json file can have the following fields:
    - signal (mandatory)
    - edge   (optional)
    - head   (optional)
    - foot   (optional)
    - assign (not supported, it is for drawing schematics)
    - config (not supported, it is just for cosmetic purposes)
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
  - if dict, signalelement is a wavelane
  - if list, signalelement is a group of wavelanes

a group is a list that has:
  - a name as first element (mandatory)
  - and either:
    - one or more groups, or
    - one or more wavelanes
"""
WAVELANE = "wavelane"
GROUP    = "group"
STRING   = "string"

"""
a wavelane may:
  - be an empty wavelane, or
  - have at least a name field
  - wave, data, node are optional
  - period and phase are also optional (and we won't support them)

    - period should be an integer. fractionary periods are ceil()'d up
      internally (i.e. 2.9 becomes 3)
    - phase doesn't seem to have restrictions

  - type is a custom field we define where the user can specify the datatype of
    the signal. This field is not rendered by wavedrom
"""
NAME     = "name"
WAVE     = "wave"
DATA     = "data"
NODE     = "node"
PERIOD   = "period"
PHASE    = "phase"
TYPE     = "type"

"""
a wave is a string that contains one character per clock cycle for the signal
  - each character does a different thing
  - any other characters are interpreted the same as 'x'
  - we won't be supporting neither REDUCE nor STRETCH
"""
PCLK     = 'p'  # clock, active on rising_edge
PCLKEDGE = 'P'  # clock, active on rising_edge with explicit arrow
NCLK     = 'n'  # clock, negative on falling_edge
NCLKEDGE = 'N'  # clock, negative on falling_edge with explicit arrow
ZERO     = '0'  # logic zero
ONE      = '1'  # logic one
LOW      = 'l'  # logic zero, vertical fall (no slope)
LOWEDGE  = 'L'  # logic zero, vertical fall, with down arrow
HIGH     = 'h'  # logic one, vertical rise (no slope)
HIGHEDGE = 'H'  # logic one, vertical rise, with down arrow
UNKNOWN  = 'x'  # unknown value
DOWN     = 'd'  # signal falling down with exponential shape
UP       = 'u'  # signal rising up with exponential shape
HIGHZ    = 'z'  # high impedance
EQUAL    = '='  # next element in data, white color
WHITE    = '2'  # next element in data, white color (same as '=')
YELLOW   = '3'  # next element in data, yellow color
ORANGE   = '4'  # next element in data, orange color
BLUE     = '5'  # next element in data, blue color
CYAN     = '6'  # next element in data, cyan color
GREEN    = '7'  # next element in data, green color
MAGENTA  = '8'  # next element in data, magenta color
RED      = '9'  # next element in data, red color
REPEAT   = '.'  # repeat previous value
MULTIPLE = '|'  # repeat previous value one or more times
REDUCE   = '<'  # following elements will be rendered twice as thin
STRETCH  = '>'  # following elements will be rendered twice as wide

"""
an edge is a list of strings

each string has these tokens:
  - <source><arrow><destination>[<whitespace><label>]

  - source must have been defined in a node inside a wavelane
  - destination must have been defined in a node inside a wavelane
  - arrow must be one of the allowable values
  - whitespace (optional) is just whitespace
  - label (optional) can be any string

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
