"""Creates an argument parser for the FVM Framework using argparse"""

import argparse

def create_parser():
    """
    Create an argument parser

    :returns: Argument parser for the FVM Framework
    :rtype: class 'argparse.ArgumentParser'
    """
    # Configure the argument parser
    parser = argparse.ArgumentParser(description='Run the FVM Framework')
    parser.add_argument('-d', '--design',
            help='If set, run the specified design. If unset, run all designs. (default: %(default)s)')
    parser.add_argument('-s', '--step',
            help='If set, run the specified step. If unset, run all steps. (default: %(default)s)')
    parser.add_argument('-c', '--cont', default=False, action='store_true',
            help='Continue with next steps even if errors are detected. (default: %(default)s)')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
            help='Show full tool outputs. (default: %(default)s)')
    parser.add_argument('-q', '--quiet', default=False, action='store_true',
            help='Show only error tool outputs. (default: %(default)s)')
    parser.add_argument('-l', '--list', default=False, action='store_true',
            help='Only list available methodology steps, but do not execute them. (default: %(default)s)')
    parser.add_argument('-o', '--outdir', default = "fvm_out",
            help='Output directory. (default: %(default)s)')
    parser.add_argument('-g', '--gui', default=False, action='store_true',
            help='Show tool results with GUI after tool execution. (default: %(default)s)')
    parser.add_argument('-n', '--guinorun', default=False, action='store_true',
            help='Show already existing tool results with GUI, without running the tools again. (default: %(default)s)')
    parser.add_argument('--show', default=False, action='store_true',
            help='Show the HTML dashboard after execution of the formal tools. (default: %(default)s)')
    parser.add_argument('--shownorun', default=False, action='store_true',
            help='Show the existing HTML dashboard, without running the formal tools. (default: %(default)s)')
    parser.add_argument('--showall', default=False, action='store_true',
            help='Show the existing HTML dashboard of every design in the output directory, without running the formal tools. (default: %(default)s)')

    return parser
