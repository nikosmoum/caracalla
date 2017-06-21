#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
# Red Hat trademarks are not licensed under GPLv3. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

"""
Command line for parsing results of candlepin ferformance tests.
"""

from __future__ import print_function

import logging
import csv
import json

from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger('parse-jtl')


def parse_options():
    usage = "%(prog)s [options]  results_file"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("--pretty-print",
                        action="store_true",
                        dest="pretty_print",
                        help="Parse and pretty print")
    parser.add_argument("-p", "--parse",
                        action="store_true",
                        dest="parse",
                        help="Parse to compute a dictionary")
    parser.add_argument("-c", "--compare",
                        action="store_true",
                        dest="compare",
                        help="Compare results with baseline dictionary")
    parser.add_argument("-e", "--expected", default=None,
                        dest="expected",
                        help="Success criteria dictionary, only used with -c")
    parser.add_argument("-b", "--baseline", default=None,
                        dest="baseline",
                        help="Dictionary to compare with, only used with -c")
    parser.add_argument("-o", "--output",
                        dest="output",
                        help="Output file to write the result to.")

    options, args = parser.parse_known_args()

    if len(args) != 1:
        parser.error("You must provide only one results file to parse/compare")

    if options.parse is None and options.compare is None and options.pretty_print is None:
        parser.error("You have to choose one of the commands: -p, --pretty-print or -c")

    if options.compare is True:
        if not options.baseline and options.expected:
            parser.error("Options: -b and -e have to be provided with -c")

    return options, args


def compare_success(key, input_value, required_success):
    if input_value < required_success:
        return "key: %s, success rate: %s, expected: %s\n" \
            % (key, input_value, required_success)
    return ""


def compare_average(key, input_value, base_value, allowed_deviance):
    if base_value == 0:
        base_value = 1
    deviance = ((input_value - base_value) * 100) / base_value
    if deviance > allowed_deviance:
        return "key: %s, elapsed: %s, base line: %s, allowed deviance: %s\n" \
            % (key, input_value, base_value, allowed_deviance)
    return ""


def compare_csv(input_dict, baseline_dict, deviance_dict):
    result = ""
    for key, values in input_dict.items():
        result += compare_success(key,
                                  values['success_%'],
                                  deviance_dict[key]['required_success'])
        result += compare_average(key,
                                  values['average'],
                                  baseline_dict[key]['average'],
                                  deviance_dict[key]['allowed_deviance'])
    return result


def parse_csv(input_file):
    results = {}
    with open(input_file, 'rb') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row[2] not in results:
                results[row[2]] = {'count': 0, 'elapsed': 0, 'success': 0}
            results[row[2]]["count"] += 1
            results[row[2]]["elapsed"] += int(row[1])
            if row[7] == "true":
                results[row[2]]["success"] += 1
    for key, result in results.items():
        results[key]["success_%"] = (result["success"] * 100) / result["count"]
        results[key]["average"] = (result["elapsed"]) / result["count"]
    return results


def main():
    (options, args) = parse_options()
    input_file = args[0]
    logger.debug("Opening %s" % input_file)
    current_results = parse_csv(input_file)
    successful_compare = False

    if options.parse:
        output_txt = json.dumps(current_results, sort_keys=True, indent=2)
    elif options.pretty_print:
        output_txt = "success %, average time elapsed, API\n"
        for key, result in sorted(current_results.items()):
            output_txt += "%s, %s, %s \n" \
                % (result["success_%"], result["average"], key)
    elif options.compare:

        # Load file with baseline results
        with open(options.baseline, 'r') as baseline_file:
            baseline_data = json.load(baseline_file)

        # Load file with expected success rates for all performance tests
        with open(options.expected, 'r') as expected_success_rate_file:
            expected_success_rate = json.load(expected_success_rate_file)

        # Compare current results with baseline results
        output_txt = compare_csv(current_results, baseline_data, expected_success_rate)

        # When current results are in limits, then output_txt is empty string
        if not output_txt:
            successful_compare = True
            print('All results in file: %s are in limits of allowed deviations.' % input_file)
    else:
        return

    if options.output is not None:
        output_file = open(options.output, 'w+')
        output_file.write(str(output_txt))
    elif not successful_compare:
        print(output_txt)

    if options.compare and not successful_compare:
        raise Exception(output_txt)


if __name__ == "__main__":
    main()
