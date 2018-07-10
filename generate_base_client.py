#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import glob
import os
import subprocess
import sys

cmdline_desc = """\
Runs Stone to generate Python types and client for the Dropbox client. 
"""

_cmdline_parser = argparse.ArgumentParser(description=cmdline_desc)
_cmdline_parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Print debugging statements.',
)
_cmdline_parser.add_argument(
    'spec',
    nargs='*',
    type=str,
    help='Path to API specifications. Each must have a .stone extension.',
)
_cmdline_parser.add_argument(
    '-s',
    '--stone',
    type=str,
    help='Path to clone of stone repository.',
)

# List of namespaces for business endpoints
TEAM_NAMESPACES = [
    'team',
    'team_common',
    'team_log',
    'team_policies',
]

def main():
    """The entry point for the program."""

    args = _cmdline_parser.parse_args()
    verbose = args.verbose

    if args.spec:
        specs = args.spec
    else:
        # If no specs were specified, default to the spec submodule.
        specs = glob.glob('spec/*.stone')  # Arbitrary sorting
        specs.sort()

    specs = [os.path.join(os.getcwd(), s) for s in specs]

    stone_path = os.path.abspath('stone')
    if args.stone:
        stone_path = args.stone

    dropbox_pkg_path = os.path.abspath(
        os.path.join(os.path.dirname(sys.argv[0]), 'dropbox'))
    if verbose:
        print('Dropbox package path: %s' % dropbox_pkg_path)

    if verbose:
        print('Generating Python types')
    subprocess.check_output(
        (['python', '-m', 'stone.cli', 'python_types', dropbox_pkg_path] +
         specs + ['-a', 'host', '-a', 'style'] +
         ['--', '-r', 'dropbox.dropbox.Dropbox.{ns}_{route}']),
        cwd=stone_path)

    if verbose:
        print('Generating Python client')

    blacklist_namespace_args = []
    for namespace in TEAM_NAMESPACES:
        blacklist_namespace_args.extend(('-b', namespace))
    o = subprocess.check_output(
        (['python', '-m', 'stone.cli', 'python_client', dropbox_pkg_path] +
         specs + ['-a', 'host', '-a', 'style'] + blacklist_namespace_args +
         ['--', '-m', 'base', '-c', 'DropboxBase', '-t', 'dropbox']),
        cwd=stone_path)
    if o:
        print('Output:', o)

    whitelist_namespace_args = []
    for namespace in TEAM_NAMESPACES:
        whitelist_namespace_args.extend(('-w', namespace))
    o = subprocess.check_output(
        (['python', '-m', 'stone.cli', 'python_client', dropbox_pkg_path] +
         specs + ['-a', 'host', '-a', 'style'] + whitelist_namespace_args +
         ['--', '-m', 'base_team', '-c', 'DropboxTeamBase', '-t', 'dropbox']),
        cwd=stone_path)
    if o:
        print('Output:', o)

if __name__ == '__main__':
    main()
