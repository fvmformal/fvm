"""
Functions to actually convert the .json wavedroms into PSL sequences
"""

# To use the JSON encoder and decoder
import json

# Allow to obtain basename of input files
from pathlib import Path
import os

# To use sys.exit and be able to print to sys.stderr
import sys

# To easily get command-line arguments
import argparse

# To allow pretty cool debug prints than can be disabled after development
from icecream import ic

# Since JSON is a subset of YAML, use pyyaml since it accepts missing quotes
import yaml

# Allow to render wavedrom signals from inside python
import wavedrom

# Import the wavedrom definitions we need
from fvm.drom2psl.definitions import GROUP, WAVE, NAME

# Import our own functions to traverse the dictionary
from fvm.drom2psl.traverse import traverse

# Import our own functions to interpret the dictionary
from fvm.drom2psl.interpret import (get_signal, check_wavelane, get_type,
                                    get_group_name, flatten, get_wavelane_wave,
                                    get_wavelane_name, get_wavelane_data,
                                    get_group_arguments, get_clock_value,
                                    is_pipe, gen_sere_repetition,
                                    get_signal_value, adapt_value_to_hdltype)

# Import our own logging functions
from fvm.drom2psl.basiclogging import info, error #, warning

def generator(filename, outdir = None, verbose_psl = True, debug = False,
              do_traverse = False):
    """
    Actually generate the PSL file with the sequences

    :param filename: input wavedrom file (JSON)
    :type filename: string
    :param outdir: output directory (if not specified, each .psl file will be
                   generated in the same directory of each input file)
    :type outdir: string
    :param verbose_psl: add extra comments to generated psl file
    :type verbose_psl: bool
    :param debug: print debug messages
    :type debug: bool
    :param do_traverse: traverse the wavedrom file, printing structural debug
                        information
    :type do_traverse: bool

    :returns: 0 if no errors detected, 1 if errors were detected, 2 if the dict
              extracted from the json file was empty
    :rtype: int
    """

    ic("generator")
    ic(filename, outdir, verbose_psl, debug, do_traverse)

    # Disable icecream if we are not debugging
    if debug is False:
        ic.disable()

    # Set custom prefix for icecream
    ic.configureOutput(prefix='generator | ')

    # Open the input file
    f = open(filename, encoding="utf-8")
    full_filename = Path(filename).resolve()
    ic(full_filename)

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

    source = json.loads(wavedrom.fixQuotes(filename))
    ic(source)

    try:
        ok = True
        dictionary = yaml.load(f, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        ok = False

    if not ok:
        error("Invalid YAML syntax in file: "+str(filename))
    if ok:
        ic(dictionary)

    if ok:
        if dictionary is None:
            error("Input JSON file is empty!")
            empty_json = True
        else:
            empty_json = False

    #debug("Extracting dictionary interpreting it as JSON")
    #dictionary = json.load(f)
    #debug(type(dictionary))
    #debug(dictionary)

    # Since wavedrompy reads a string and not a dict, let's read the file again,
    # this time into a string

    if ok:
        ic("Rendering input file -> string -> wavedrompy")
        with open(filename, "r", encoding="utf-8") as f:
            string = f.read()

    # Close the input file
    f.close()

    # Let's process the dict now
    # We probably should do this recursively

    #detect_groups()
    if ok:
        ic("Traversing dictionary")

    if do_traverse:
        print("TRAVERSE: Interpreting dict")
        traverse("  ", dictionary)

    # Process dictionary
    if ok:
        ic("Getting the signal list")
        signal, ok = get_signal(dictionary)

    #if error == False and debug :
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
                error("  wavelane "+str(wavelane.get(NAME))+
                      " has a wave with length "+str(len(wavelane.get(WAVE)))+
                      " (wave is "+str(wavelane.get(WAVE))+" )")
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

        vunit_name = full_filename.stem

        if outdir is not None:
            output_file = os.path.join(outdir,
                                       os.path.basename(Path(full_filename).with_suffix('.psl')))
        else:
            output_file = Path(full_filename).with_suffix('.psl')

        ic(output_file)

        vunit = ''
        vunit +=  '-- Automatically created by drom2psl\n'
        vunit += f'-- Input file: {full_filename}\n'
        vunit +=  ('-- These sequences and/or properties can be reused from'
                       ' other PSL files by doing:\n')
        vunit += f'-- inherit {vunit_name};\n\n'
        vunit += f'vunit {vunit_name} ' + '{\n\n'

        # We are assuming a number of things to make this usable, see the
        # module docstring

        # To cover the special case where we have no groups, in that case let's
        # define a group whose name is the empty string
        if num_groups == 0:
            groups.append('')

        for groupname in groups:
            if groupname == '':
                sequence_name = f'{vunit_name}'
            else:
                sequence_name = f'{vunit_name}_{groupname}'

            # Get group arguments
            group_arguments = get_group_arguments(groupname, flattened_signal)
            ic(group_arguments)

            # If there are no group arguments, we don't want to print the
            # parentheses
            if len(group_arguments) == 0:
                vunit += f'  sequence {sequence_name}\n'
            else:
                vunit += f'  sequence {sequence_name} (\n'
                vunit += format_group_arguments(group_arguments)

            # If we are in the last element, we don't want a semicolon
            # so we remove the last two characters: ';\n', then we add the \n
            # again
            if vunit[-2:] == ";\n":
                vunit = vunit[:-2]
                vunit += '\n'

            if len(group_arguments) == 0:
                vunit += '  is {\n'
            else:
                vunit +=  '  ) is {\n'

            prev_line = ''
            prev_cycles = 0
            prev_or_more = False
            for cycle in range(clock_cycles):

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
                        value = adapt_value_to_hdltype(value)
                        if value != "'-'":
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
                or_more = is_pipe(flattened_signal[0], cycle)

                # If lines are different, then just:
                #   1. Finish the previous line with the cycles
                #   2. Write the current line, except the cycles
                #   3. The actual current line will be the next prev_line
                if line != prev_line:
                    if prev_line != '':
                        prev_cycles_text = gen_sere_repetition(prev_cycles,
                                                                prev_or_more,
                                                                True)
                        vunit += prev_cycles_text + '\n'

                    vunit += line
                    prev_line = line
                    prev_cycles = cycles
                    prev_or_more = or_more

                # If lines are equal:
                #   Do not finish the previous line, just add the cycles to
                #   prev_cycles and compute the relevant 'or_more': both lines
                #   are equal so if at least one of them allows repeat, then
                #   the merged line must allow repeat
                else:
                    prev_cycles += cycles
                    prev_or_more = bool(prev_or_more or or_more)

            # After the for loop finishes, we will have the last cycles to
            # write, so let's write them:
            prev_cycles_text = gen_sere_repetition(prev_cycles, prev_or_more,
                                                    False)
            if prev_line != '':
                vunit += prev_cycles_text + '\n'

            vunit +=  '  };\n'
            vunit += '\n'

        # If we have exactly two sequences (two wavedrom groups), let's create
        # a sample property relating them
        if num_groups == 2:
            if verbose_psl:
                vunit += "  -- Relational operands between sequences may be, among others:\n"
                vunit += "  --   && : both must happen and last exactly the same number of cycles\n"
                vunit += "  --   & : both must happen, without any requirement on their durations\n"
                vunit += ("  --   |-> : implication: both must happen, with"
                          " the first cycle of the second occurring during the"
                          " last cycle of the first\n")
                vunit += ("  --   |=> : non-overlapping implication: both must"
                          " happen, with the first cycle of the second occuring"
                          " the cycle after the last cycle of the first\n")
            vunit += f'  property {vunit_name} (\n'
            for groupname in groups:
                group_arguments = get_group_arguments(groupname, flattened_signal)
                ic(group_arguments)
                vunit += format_group_arguments(group_arguments)
            # Again, remove the unneded semicolon and restore the deleted \n
            if vunit[-2:] == ";\n":
                vunit = vunit[:-2]
                vunit +=  '\n'
            vunit +=  '  ) is\n' # {\n'
            group0_args = format_group_arguments_in_call(get_group_arguments(groups[0],
                                                                             flattened_signal))
            group1_args = format_group_arguments_in_call(get_group_arguments(groups[1],
                                                                             flattened_signal))
            vunit += f'    always {{ {{{vunit_name}_{groups[0]}{group0_args}}}'
            vunit += f' && {{{vunit_name}_{groups[1]}{group1_args}}} }};\n'
            vunit += '\n'


        vunit += '}\n'

        ic(flattened_signal[0])

        with open(output_file, 'w', encoding="utf-8") as f:
            f.write(vunit)

    ic("Was the execution correct?")
    ic(ok)

    # Render the json using wavedrompy. This way we should receive an error if
    # there are any wavedrom-specific errors in an otherwise correct JSON
    if ok:
        if (not empty_json) and debug:
            ic("Rendering the JSON into an .svg")
            render = wavedrom.render(string)
            ic(render)
            ic(full_filename)
            svgfilename = Path(full_filename).with_suffix('.svg')
            ic(svgfilename)
            if debug:
                render.saveas(svgfilename)

    #    for i in range(len(value)):
    #        print("i:", i, "value[i]:", value[i])
    #        print("type(value[i]):", type(value[i]))

    # Return different values to the shell, depending on the type of error
    if not ok:
        ret = 1
    elif empty_json:
        ret = 2
    else:
        ret = 0

    if ret != 0 :
        error("At least one error!")
    else:
        if debug:
            info("No errors detected!")

    return ret

def format_group_arguments(group_arguments):
    """Returns the group arguments with an extra semicolon that should be
    removed separately. Avoids duplicated arguments."""

    seen = set()
    string = ''

    for j in group_arguments:
        argument, datatype = j

        if argument in seen:
            continue

        seen.add(argument)
        string += f'    hdltype {datatype} {argument};\n'

    return string

def format_group_arguments_in_call(group_arguments):
    """Returns the group arguments ready to parameterize a property or
    sequence, for example: (addr, data)"""
    string = ''
    # Only return a non-empty string if there it at least one argument
    if len(group_arguments) > 0:
        string += '('
        for j in group_arguments:
            argument = j[0]
            string += f'{argument}, '
        # Remove the last command and space, and add the closing parenthesis
        string = string[:-2]
        string += ')'
    return string

def create_parser():
    """Configure drom2psl's argument parser"""
    parser = argparse.ArgumentParser(description=('Generate PSL sequences from'
                                     ' .json wavedrom descriptions.'))
    parser.add_argument('inputfiles', nargs='+',
                        help='.json input file(s) (must be wavedrom compatible)')
    parser.add_argument('--outdir', default=None,
                        help=('Output directory for generated files. By'
                              ' default, outputs are generated in the same'
                              ' directories where the input files are.'))
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help='Show debug messages. (default: %(default)s)')
    parser.add_argument('-t', '--traverse', default=False, action='store_true',
                        help=('Traverse the wavedrom file, printing even more'
                              ' debug information. (default: %(default)s)'))
    parser.add_argument('-q', '--quiet_psl', default=False, action='store_true',
                        help=('Do not include extra comments in generated PSL'
                              ' files. (default: %(default)s)'))

    return parser


def main():
    """
    main() function for drom2psl generator. To be used when called from the
    command-line
    """
    parser = create_parser()

    args = parser.parse_args()

    if not args.debug:
        ic.disable()

    ic(args)

    for file in args.inputfiles:
        retval = generator(file, verbose_psl=not args.quiet_psl,
                           debug=args.debug, do_traverse=args.traverse)
        if retval != 0:
            break

    sys.exit(retval)

if __name__ == "__main__":
    main()

