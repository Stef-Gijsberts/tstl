#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import os
import sys
import subprocess as sp
import shutil


def find_testpaths_in(path_root):
    paths = (
        p for p in os.listdir(path_root) if p.endswith(".tstl") and not os.path.isdir(p)
    )
    yield from paths


KINDS = {
    ">>> ": "input",
    "!>>": "end_input",
    "<<< ": "output",
    "!<<": "end_output",
}


def read_test(path_test):
    with open(path_test, "r") as f:
        for idx_line, line in enumerate(f.readlines()):
            # Ignore comments
            if line.startswith("#"):
                continue

            # Ignore empty lines
            if line.strip() == "":
                continue

            absolute_testpath = os.path.abspath(path_test)
            origin = f"{absolute_testpath}:{idx_line+1}"

            kind_token, s = None, None

            for maybe_this_kind_token in KINDS:
                if line.startswith(maybe_this_kind_token):
                    len_token = len(maybe_this_kind_token)
                    kind_token, s = line[:len_token], line[len_token:]

            if not kind_token:
                raise ValueError(
                    f"\nInvalid test at {origin}. Expected line to start with one of {', '.join(KINDS)}."
                )

            kind = KINDS[kind_token]
            yield (kind, s, origin)


def run_test(path_test, command):
    result_lines = []

    p = sp.Popen(command, stdout=sp.PIPE, stdin=sp.PIPE, stderr=sp.STDOUT)

    for kind, s, origin in read_test(path_test):
        if kind == "input":
            p.stdin.write(s.encode("utf-8"))

        elif kind == "end_input":
            try:
                p.stdin.close()
            except BrokenPipeError as e:
                result_lines.append(f"At {origin}")
                result_lines.append(
                    f"Tried to close the standard input but it is already closed!"
                )
                return False, result_lines

        elif kind == "output":
            line = p.stdout.readline().decode("utf-8")

            if line != s:
                expected = s[:-1]
                got = line[:-1]

                result_lines.append(f"At {origin}")
                result_lines.append(f'Expected\t"{expected}"')
                result_lines.append(f'Got\t\t"{got}"')
                return False, result_lines

        elif kind == "end_output":
            linebytes = p.stdout.readline()

            if not linebytes:
                continue

            line = linebytes.decode("utf-8")
            got = line[:-1]

            result_lines.append(f"Test failed at {origin}")
            result_lines.append(f"Expected End-Of-File")
            result_lines.append(f'Got\t\t"{got}"')
            return False, result_lines

    return True, result_lines


def cmd_run(args):
    if len(args) <= 1:
        print(
            "Invalid number of parameters provided to subcommand 'run'.",
            file=sys.stdout,
        )
        print(f"USAGE: {args[0]} <command to test>", file=sys.stdout)
        return

    command = args[1:]

    if not shutil.which(command[0]):
        print(f"Error: '{command[0]}' is not executable. Exiting.", file=sys.stderr)
        return

    paths_test = list(find_testpaths_in("."))

    num_tests_total = len(paths_test)
    num_tests_passed = 0

    for path_test in paths_test:
        print(f"\nRunning test {path_test} ... ", end="", flush=True)

        passed, output = run_test(path_test, command)

        if not passed:
            print("FAILED.")

            for line in output:
                print("\t" + line)
        else:
            num_tests_passed += 1
            print("passed.")

        print()

    print(f"[{num_tests_passed}/{num_tests_total}] tests passed.")


def cmd_new(args):
    filename = args[1] if len(args) > 1 else "basic.tstl"

    if os.path.exists(filename):
        print(f"{filename} already exists.")
        return

    with open(filename, "w") as f:
        print("# Test for wc", file=f)
        print(">>> Lorem ipsum dolor sit amet.", file=f)
        print("!>>", file=f)
        print("<<<       1       6      32", file=f)
        print("!<<", file=f)

    print(f"An example test was created in {filename}.")


SUBCOMMANDS = {
    "run": cmd_run,
    "r": cmd_run,
    "new": cmd_new,
    "init": cmd_new,
    "i": cmd_new,
}


USAGE = """USAGE:
    tstl [SUBCOMMAND]

Subcommands:
    run, r     run the tests
    init, i    create an initial test file

Examples:
    tstl run wc                         run the tests in the current directory
                                        on the command wc
    tstl run python3 ./myscript.py      run the tests in the current directory
                                        on the command 'python3 ./myscript.py'
"""


def main():
    argv = sys.argv

    if len(argv) <= 1:
        print(USAGE, file=sys.stderr)
        return

    name_subcommand = argv[1]
    subcommand = SUBCOMMANDS[name_subcommand]
    args_subcommand = argv[1:]

    try:
        subcommand(args_subcommand)
    except ValueError as e:
        print(e, file=sys.stdout)


if __name__ == "__main__":
    main()
