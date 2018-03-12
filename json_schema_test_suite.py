#!/usr/bin/env python -u
# coding: utf-8

"""Run a JSON Schema test suite and print results."""

from collections import Counter, defaultdict, namedtuple
from enum import Enum, auto
from pathlib import Path
from textwrap import dedent
import argparse
import configparser
import json
import sys

from colorama import Fore
import fastjsonschema

class TestResult(Enum):
    FALSE_POSITIVE = auto()
    TRUE_POSITIVE = auto()
    FALSE_NEGATIVE = auto()
    TRUE_NEGATIVE = auto()
    UNDEFINED = auto()
    IGNORED = auto()

Test = namedtuple("Test", "description exception result ignore")


def _get_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--strict", help="Do not ignore test files, even if configured to do so", action="store_false")
    p.add_argument("--verbose", help="Print all test results", action="store_true")
    p.add_argument("path", help="Path to either a configuration file or a single JSON test file", type=Path)
    return p


def _main():
    ignore_file_paths = set()

    config = configparser.ConfigParser()
    try:
        config.read(str(args.path))
        suite_dir_path = Path(config.get("suite", "dir")).resolve()
        test_file_paths = sorted(set(suite_dir_path.glob("**/*.json")))
        if args.strict:
            for l in config.get("ignore", "files").splitlines():
                p = Path(suite_dir_path / l).resolve()
                if p.is_file():
                    ignore_file_paths.add(p)
    except configparser.MissingSectionHeaderError:
        test_file_paths = {args.path.resolve()}

    tests = defaultdict(dict)
    test_results = Counter()

    schema_exceptions = {}
    for test_file_path in test_file_paths:
        with test_file_path.open() as f:
            tests[test_file_path.name] = defaultdict(dict)
            ignore = True if test_file_path in ignore_file_paths else False
            test_data = json.load(f)
            for test_case in test_data:
                test_case_description = test_case["description"]
                schema = test_case["schema"]
                tests[test_file_path.name][test_case_description] = []
                try:
                    validate = fastjsonschema.compile(schema)
                except Exception as e:
                    schema_exceptions[test_file_path] = e
                for test in test_case["tests"]:
                    description = test["description"]
                    data = test["data"]
                    result = exception = None
                    try:
                        if test["valid"]:
                            try:
                                validate(data)
                                result = TestResult.TRUE_POSITIVE
                            except fastjsonschema.exceptions.JsonSchemaException as e:
                                result = TestResult.FALSE_NEGATIVE
                                exception = e
                        else:
                            try:
                                validate(data)
                                result = TestResult.FALSE_POSITIVE
                            except fastjsonschema.exceptions.JsonSchemaException as e:
                                result = TestResult.TRUE_NEGATIVE
                                exception = e
                    except Exception as e:
                        result = TestResult.UNDEFINED
                        exception = e
                    tests[test_file_path.name][test_case_description].append(Test(description, exception, result, ignore))
                    test_results.update({TestResult.IGNORED if ignore else result: 1})

    for file_name, test_cases in sorted(tests.items()):
        for test_case in test_cases.values():
            if any(t for t in test_case if t.ignore):
                print(Fore.MAGENTA + "⛔" + Fore.RESET, file_name)
                break
            else:
                if any(t for t in test_case if t.result in (TestResult.FALSE_POSITIVE, TestResult.FALSE_NEGATIVE)):
                    print(Fore.RED + "✘" + Fore.RESET, file_name)
                    break
                elif any(t for t in test_case if t.result == TestResult.UNDEFINED):
                    print(Fore.YELLOW + "⚠" + Fore.RESET, file_name)
                    break
                else:
                    print(Fore.GREEN + "✔" + Fore.RESET, file_name)
                    break
        for test_case_description, test_case in test_cases.items():
            if not any(t for t in test_case if t.ignore):
                if any(t for t in test_case if t.result in (TestResult.FALSE_POSITIVE, TestResult.FALSE_NEGATIVE)):
                    print("  " + Fore.RED + "✘" + Fore.RESET, test_case_description)
                elif any(t for t in test_case if t.result == TestResult.UNDEFINED):
                    print("  " + Fore.YELLOW + "⚠" + Fore.RESET, test_case_description)
                elif args.verbose:
                    print("  " + Fore.GREEN + "✔" + Fore.RESET, test_case_description)
                for test in test_case:
                    if test.result in (TestResult.FALSE_POSITIVE, TestResult.FALSE_NEGATIVE):
                        print("    " + Fore.RED + "✘" + Fore.RESET,
                              Fore.CYAN + test.result.name + Fore.RESET,
                              Fore.RED + type(test.exception).__name__ + Fore.RESET,
                              "{}: {}".format(test.description, test.exception))
                    elif test.result == TestResult.UNDEFINED:
                        print("    " + Fore.YELLOW + "⚠" + Fore.RESET,
                              Fore.CYAN + test.result.name + Fore.RESET,
                              Fore.YELLOW + type(test.exception).__name__ + Fore.RESET,
                              "{}: {}".format(test.description, test.exception))
                    elif args.verbose:
                        print("    " + Fore.GREEN + "✔" + Fore.RESET,
                              Fore.CYAN + test.result.name + Fore.RESET,
                              test.description)

    if schema_exceptions:
        print("\nSchema exceptions:\n")
        for file_path, exception in sorted(schema_exceptions.items()):
            if file_path in ignore_file_paths:
                print(Fore.MAGENTA + "⛔" + Fore.RESET, end=" ")
            else:
                print(Fore.RED + "✘" + Fore.RESET, end=" ")
            try:
                print("{}: {}: '{}'".format(file_path.name, exception, exception.text.strip()))
            except AttributeError:
                print("{}: {}".format(file_path.name, exception))

    total = sum(test_results.values())
    sub_total = total - test_results[TestResult.IGNORED]
    total_failures = total_passes = 0
    print("\nSummary of {} tests:\n".format(total))

    print("Failures:\n")
    for result in (TestResult.FALSE_POSITIVE, TestResult.FALSE_NEGATIVE, TestResult.UNDEFINED):
        total_failures += test_results[result]
        if result == TestResult.UNDEFINED:
            print(Fore.YELLOW + "⚠", end=" ")
        else:
            print(Fore.RED + "✘", end=" ")
        print(Fore.CYAN + "{:<14}".format(result.name) + Fore.RESET,
              "{:>4} {:>6.1%}".format(test_results[result], test_results[result] / sub_total))
    print("                 {:>4} {:>6.1%}".format(total_failures, total_failures / sub_total))

    print("\nPasses:\n")
    for result in (TestResult.TRUE_POSITIVE, TestResult.TRUE_NEGATIVE):
        total_passes += test_results[result]
        print(Fore.GREEN + "✔",
              Fore.CYAN + "{:<14}".format(result.name) + Fore.RESET,
              "{:>4} {:>6.1%}".format(test_results[result], test_results[result] / sub_total))
    print("                 {:>4} {:6.1%}".format(total_passes, total_passes / sub_total))

    print("\n" + Fore.MAGENTA + "⛔" + Fore.RESET,
          "Ignored: {:>10}".format(test_results[TestResult.IGNORED]))
    print("Coverage: {:>7}/{} {:>6.1%}".format(total_failures + total_passes, total,
                                               (total_failures + total_passes) / total))

    return total_failures > 0


if __name__ == "__main__":
    args = _get_parser().parse_args()
    sys.exit(_main())
