# Set to True to print debug messages
DEBUG = True

# Set to True to print the result of traversing the dictionary
TRAVERSE = False

# To use the JSON encoder and decoder
import json

# Since JSON is a subset of YAML, use pyyaml since it accepts missing quotes
import yaml

# To use sys.exit and be able to print to sys.stderr
import sys

# Use yamllint to detect common YAML errors, such as key in dict defined more
# than once
import yamllint
from yamllint import config

# To easily get command-line arguments
import argparse

# Allow to render wavedrom signals from inside python
import wavedrom

# Allow to obtain basename of input files
from pathlib import Path
import os

# Very cool debug function
# Documentation here: https://pypi.org/project/varname/
#from varname.helpers import debug

# Allow to compare data type to Dict
#from typing import Dict

# Import our own constant definitions
#from definitions import *

# Import our own functions to traverse the dictionary
from fvm.drom2psl.traverse import traverse

# Import our own functions to interpret the dictionary
from fvm.drom2psl.interpret import *

# Import our own logging functions
from fvm.drom2psl.logging import *

# To allow pretty cool debug prints than can be disabled after development
# Explanation at: https://towardsdatascience.com/do-not-use-print-for-debugging-in-python-anymore-6767b6f1866d
from icecream import ic

def generator(FILES, debug = False):

  TRAVERSE = debug

  # If FILES is a single file, convert it to a list
  if isinstance(FILES, str):
      FILES = [FILES]

  # Disable icecream if we are not debugging
  if DEBUG == False:
      ic.disable

  # Set custom prefix for icecream
  ic.configureOutput(prefix='Debug | ')

#  ic("Test icecream")
#  print("Test print")
#  info("Test info")
#  warning("Test warning")
#  error("Test error")


  #ic(args)
  ic(FILES)

  # Open the input files
  for FILE in FILES :
    f = open(FILE)

    # Pass the input file through the linter
    #conf = config.YamlLintConfig('extends: default')
    #for p in yamllint.linter.run(f, conf):
    #    print(p.desc, p.line, p.rule)

    #gen = linter.run(f, conf)
    #debug(type(gen))
    #debug(gen)



    # Extract the dictionary from the file. This should detect any JSON syntax
    # errors
    # We'll use the YAML parser instead of the JSON parser since the JSON
    # parser is very strict with the double quotes (expects all keys to be
    # inside double quotes), but the wavedrom format doesn't require those
    # double quotes

    ic("Extracting dictionary interpreting it as YAML")

    # Load YAML and output JSON, to fix typical json format errors, so we can
    # accept mosty-correct json. We do this because the online wavedom website also
    # does it, even the examples are not correct (they do not put the keys in
    # quotes, which is valid YAML but invalid JSON, and in example step7_head_foot
    # they don't put a space after the colons, which is invalid YAML but I believe
    # it is correct JSON. Loading YAML and outputting JSON seems to correct the
    # issues.

    #dict = yaml.load(f, Loader=yaml.SafeLoader)
    #debug(type(dict))
    #debug(dict)
    #string = json.dumps(dict, indent=4)
    #debug(type(string))
    #debug(string)
    #fixed_dict = json.loads(string)
    #debug(type(fixed_dict))
    #debug(fixed_dict)

    source = json.loads(wavedrom.fixQuotes(FILE))
    ic(source)

    try:
      ok = True
      dict = yaml.load(f, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
      ok = False

    if not ok:
      error("Invalid YAML syntax in file: "+str(FILE))
    if ok:
      ic(dict)

    if ok:
      if dict is None:
        error("Input JSON file is empty!")
        empty_json = True
      else:
        empty_json = False

    #debug("Extracting dictionary interpreting it as JSON")
    #dict = json.load(f)
    #debug(type(dict))
    #debug(dict)

    # Since wavedrompy reads a string and not a dict, let's read the file again,
    # this time into a string

    if ok:
      ic("Rendering input file -> string -> wavedrompy")
      with open(FILE, "r") as f:
        string = f.read()

    # Close the input file
    f.close()

    #ic(type(string))
    #ic(string)

    # Let's process the dict now
    # We probably should do this recursively

    #detect_groups()
    if ok:
      ic("Traversing dictionary")

    if TRAVERSE:
        print("DEBUG: Interpreting dict")
        traverse("  ", dict)

    # Process dictionary
    if ok:
      ic("Getting the signal list")
      signal, ok = get_signal(dict)

    #if error == False and DEBUG :
    #    ic("Listing signal elements")
    #    list_elements("ListElements:", signal)

    if ok:
        ic("Counting the number of primary groups")
        num_groups = 0
        groups = []
        for i, value in enumerate(signal):
            if get_type(value) == GROUP:
                num_groups += 1
                groups.append(get_group_name(value))
        ic(num_groups)
        ic(groups)

    if ok:
      ic("Flattening signal")
      flattened_signal, ok = flatten("", signal, None)

    if ok:
      ic(flattened_signal)
      ic("Detected", len(flattened_signal), "wavelanes")

    if ok:
        ic("Checking wavelanes in flattened signal")
        for wavelane in flattened_signal:
            ok = check_wavelane(wavelane)
        if not ok:
            error("At least a wavelane error")

    if ok:
        ic("Checking all non-empty wavelanes' waves have the same length")
        lengths = []
        for wavelane in flattened_signal :
            if len(wavelane) != 0 :
                #ic(wavelane.get(WAVE))
                #ic(type(wavelane.get(WAVE)))
                #ic(len(wavelane.get(WAVE)))
                lengths.append(len(wavelane.get(WAVE)))
        ic("Wavelane lengths", lengths)
        #ic(set(lengths))
        #ic(len(set(lengths)))
        if len(set(lengths)) != 1 :
            error("Not all wavelanes' wave fields have the same length!")
            for wavelane in flattened_signal :
                error("  wavelane "+str(wavelane.get(NAME))+" has a wave with length "+str(len(wavelane.get(WAVE)))+" (wave is "+str(wavelane.get(WAVE))+" )")
            ok = False
        else:
            ic("detected", lengths[0], "clock cycles")
            clock_cycles = lengths[0]

    if ok:
        ic("Counting wavelanes")
        allwavelanes = 0
        nonemptywavelanes = 0
        for wavelane in flattened_signal:
            allwavelanes += 1
            if len(wavelane) != 0 :
                nonemptywavelanes += 1
        ic("detected", allwavelanes, "wavelanes")
        ic("from which", nonemptywavelanes, "are non-empty")

    if ok:
        ic("Creating a psl vunit")

        vunit_name = os.path.basename(FILE)
        vunit_name, extension = os.path.splitext(vunit_name)
        output_file = vunit_name + '.psl'

        # TODO : add arguments to drom2psl and timestamp of file creation
        vunit = '-- Automatically created by drom2psl'
        vunit = '-- These sequences and/or properties can be reused from other PSL files by doing:'
        vunit = f'--   inherit {vunit_name}'
        vunit = ''
        vunit += f'vunit {vunit_name} ' + '{\n\n'

        # TODO : We are assuming a number of things to make this usable:
        #   1. That the clock is the first signal that appears in the wavedrom
        #   2. That only the clock carries the repeat zero-or-more symbol '|'
        #   3. That all non-clock signals are in groups
        #      TODO : we could just create the sequence with the signals if
        #      there are no groups
        #   4. That, if we have two top-level groups, then we are describing
        #   some relation between two sequences
        #      5. In that case, we also are assuming that the sequence that
        #      appears first in the wavedrom is the sequence that should
        #      trigger the other one

        # To cover the special case where we have no groups, in that case let's
        # define a group whose name is the empty string
        if num_groups == 0:
            groups.append('')
            group = 1

        for groupname in groups:
            sequence_name = f'{vunit_name}_{groupname}'

            vunit += f'  sequence {sequence_name} (\n'

            # Get group arguments
            group_arguments = get_group_arguments(groupname, flattened_signal)

            # TODO : let the user specify these datatypes
            # or we may even use a transacion/record
            # the thing is that we can't define that in the drom JSON

            ic(group_arguments)
            vunit += format_group_arguments(group_arguments)
            # If we are in the last element, we don't want a semicolon
            # so we remove the last two characters: ';\n', then we add the \n
            # again
            if vunit[-2:] == ";\n":
                vunit = vunit[:-2]
                vunit += '\n'

            vunit +=  '  ) is {\n'

            prev_line = ''
            prev_cycles = 0
            for cycle in range(clock_cycles):
                cycle_string = ''
                cycle_count = 0
                clk_wavelane = flattened_signal[0]

                # The clock wavelane is processed a bit different and apart
                # from the rest of the wavelanes
                line = ''
                line += '    ('
                for wavelane in flattened_signal[1:]:
                    name = get_wavelane_name(wavelane)
                    if name[:len(groupname)] == groupname:
                        wave = get_wavelane_wave(wavelane)
                        data = get_wavelane_data(wavelane)
                        value = get_signal_value(wave, data, cycle)
                        if value != '-':
                            line += f'({name} = {value}) and '
                # The last one doesn't need the ' and ' so we'll remove 5
                # characters if they are ' and '
                if line[-5:] == ' and ':
                    line = line[:-5]

                line += ')'

                # And now to compute how many cycles we have to indicate, we
                # have to do two things:
                #   1. Check if the clock is '|' (will mean zero or more)
                #   2. Compare against the previous line
                cycles = get_clock_value(flattened_signal[0], cycle)

                # If lines are different, then just:
                #   1. Finish the previous line with the cycles
                #   2. Write the current line, except the cycles
                if line != prev_line:
                    if prev_cycles == 0:
                        prev_cycles_text = '[*]'
                    else:
                        prev_cycles_text = f'[*{prev_cycles}]'

                    if prev_line != '':
                        vunit += prev_cycles_text + ';\n'

                    vunit += line
                    prev_line = line
                    prev_cycles = cycles

                # If lines are equal:
                #   1. Do not finish the previous line, just add the cycles to
                #   prev_cycles
                else:
                    prev_cycles += cycles

            # After that, we will have the last cycles to write, so let's write
            # them:
            if prev_cycles == 0:
                prev_cycles_text = '[*]'
            else:
                prev_cycles_text = f'[*{prev_cycles}]'

            if prev_line != '':
                vunit += prev_cycles_text + '\n'

            vunit +=  '  }\n'
            vunit += '\n'

        # TODO : create the sequence
        # In the case of exactly two groups, create the sequence
        # TODO : maybe allow to specify the abort signal or condition?
        if num_groups == 2:
            vunit += '  property {vunit_name} (\n'
            for groupname in groups:
                group_arguments = get_group_arguments(groupname, flattened_signal)
                vunit += format_group_arguments(group_arguments)
            # Again, remove the unneded semicolon and restore the deleted \n
            if vunit[-2:] == ";\n":
                vunit = vunit[:-2]
                vunit +=  '\n'
            vunit +=  '  ) is {\n'
            vunit += f'    always (({vunit_name}_{groups[0]} -> {vunit_name}_{groups[1]}) abort rst);\n'
            vunit += '  }\n'
            vunit += '\n'


        vunit += '}\n'

        ic(flattened_signal[0])

        with open(output_file, 'w') as f:
            f.write(vunit)

    ic("Was the execution correct?")
    ic(ok)

    # Render the json using wavedrompy. This way we should receive an error if
    # there are any wavedrom-specific errors in an otherwise correct JSON
    if ok:
        if (not empty_json) and DEBUG:
          ic("Rendering the JSON into an .svg")
          render = wavedrom.render(string)
          ic(render)
          svgfilename = Path(FILE).stem + '.svg'
          ic(svgfilename)
          if DEBUG:
              render.saveas(svgfilename)

    #    for i in range(len(value)):
    #        print("i:", i, "value[i]:", value[i])
    #        print("type(value[i]):", type(value[i]))

    # Return different values to the shell, depending on the type of error
    if not ok:
      retval = 1
    elif empty_json:
      retval = 2
    else:
      retval = 0

    if retval != 0 :
      error("At least one error!")
    else:
      info("No errors detected!")

  return(retval)


def format_group_arguments(group_arguments):
    """Returns the group arguments with an extra semicolon that should be
    removed separately"""
    string = ''
    for j in group_arguments:
        argument = j[0]
        datatype = j[1]
        string += f'    hdltype {datatype} {argument};\n'
    return string

if __name__ == "__main__":
    # Configure the argument parser
    parser = argparse.ArgumentParser(description='Generate PSL sequence from .json wavedrom descriptions.')
    parser.add_argument('inputfiles', nargs='+', help='.json input file(s) (must be wavedrom compatible)')
    parser.add_argument('--out', default='out', help='Output directory for generated files')

    # Get arguments from command-line
    args = parser.parse_args()
    FILES = args.inputfiles

    retval = generator(FILES)
    sys.exit(retval)
