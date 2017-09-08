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


class Colors(object):
    """
    This class is used encapsulating of colors definitions
    """
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NO_COLOR = False


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
                        help="Dictionary to compare with, only used with -c and --pretty-print")
    parser.add_argument("-n", "--no-colors", default=False,
                        dest="no_colors", action="store_true",
                        help="Bypass using colors in output")
    parser.add_argument("-o", "--output",
                        dest="output",
                        help="Output file to write the result to.")

    options, args = parser.parse_known_args()

    if len(args) != 1:
        parser.error("You must provide only one results file to parse/compare")

    if not options.parse and not options.compare and not options.pretty_print:
        parser.error("You have to choose one of the commands: -p, --pretty-print or -c")

    if options.compare is True:
        if not options.baseline and options.expected:
            parser.error("Options: -b and -e have to be provided with -c")

    if options.no_colors is True:
        Colors.NO_COLOR = True

    return options, args


def compare_success_rates(api_call, current_success_rate, required_success_rate):
    """
    Compare success rates between baseline performance test and
    current performance test
    :return: Error message, when current success rate is too low
    """
    if current_success_rate < required_success_rate:
        return "API call: %s [FAILED] success rate: %s%%, expected: %4.1f%%\n" \
            % (api_call.ljust(50, '.'), current_success_rate, required_success_rate)
    return ""


def compare_elapsed_times(api_call, current_elapsed_time, baseline_elapsed_time, allowed_deviance):
    """
    Compare elapsed time of API call to baseline API call.
    :return: Error message, when elapsed time is too big
    """
    if baseline_elapsed_time == 0:
        baseline_elapsed_time = 1
    deviance = ((current_elapsed_time - baseline_elapsed_time) * 100) / baseline_elapsed_time
    if deviance > allowed_deviance:
        return "API call: %s [FAILED] current avg: %sms, base line avg: %sms, " \
            "dev: %s%%, allowed dev: %4.1f%%\n" \
            % (api_call.ljust(50, '.'), current_elapsed_time,
               baseline_elapsed_time, deviance, allowed_deviance)
    return ""


def compare_csv(input_dict, baseline_dict, deviance_dict):
    result = ""
    failures = 0
    for key, values in input_dict.items():
        # Check success rate
        succ_rate = compare_success_rates(
                        key,
                        values['success_%'],
                        100.0
                    )
        if succ_rate != "":
            if Colors.NO_COLOR is False:
                succ_rate = Colors.MAGENTA + succ_rate + Colors.ENDC
            result += succ_rate
            failures += 1
        # Check elapsed time
        elap_time = compare_elapsed_times(
                        key,
                        values['average'],
                        baseline_dict[key]['average'],
                        deviance_dict[key]['allowed_deviance']
                    )
        if elap_time != "":
            if Colors.NO_COLOR is False:
                elap_time = Colors.RED + elap_time + Colors.ENDC
            result += elap_time
            failures += 1
        # When everything is OK, then add current API call to output
        if succ_rate == "" and elap_time == "":
            info = "API call: %s [OK]\n" % key.ljust(50, '.')
            if Colors.NO_COLOR is False:
                result += Colors.GREEN + Colors.BOLD + info + Colors.ENDC
            else:
                result += info
    return result, failures


def parse_csv(input_file):
    """
    Parse CSV with results of performance test
    :param input_file: CSV file
    :return: Dictionary with results
    """
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

    # Load file with baseline results
    if options.baseline:
        with open(options.baseline, 'r') as baseline_file:
            baseline_data = json.load(baseline_file)

    if options.expected:
        # Load file with expected success rates for all performance tests
        with open(options.expected, 'r') as expected_success_rate_file:
            expected_success_rate = json.load(expected_success_rate_file)

    if options.parse:
        output_txt = json.dumps(current_results, sort_keys=True, indent=2)
    elif options.pretty_print:
        if options.baseline:
            output_txt = "success % (baseline %), average time elapsed (baseline), API\n"
        else:
            output_txt = "success %, average time elapsed, API\n"
        for key, result in sorted(current_results.items()):
            if options.baseline:
                try:
                    base_result = baseline_data[key]
                except KeyError:
                    base_result = {"success_%": "??", "average": "??"}
                output_txt += "{0}% ({1}%), {2}ms ({3}ms), {4} \n".format(
                    result["success_%"],
                    base_result["success_%"],
                    result["average"],
                    base_result["average"],
                    key
                )
            else:
                output_txt += "{0}%, {1}ms, {2} \n".format(
                    result["success_%"],
                    result["average"],
                    key
                )
    elif options.compare:

        # Compare current results with baseline results
        output_txt, failures = compare_csv(current_results, baseline_data, expected_success_rate)

        # When current results are in limits, then output_txt is empty string
        if failures == 0:
            print('All results in file: %s are in limits of allowed deviations.' % input_file)
    else:
        return

    # Output results to file or stdout
    if options.output is not None:
        output_file = open(options.output, 'w+')
        output_file.write(str(output_txt))
    else:
        print(output_txt)


if __name__ == "__main__":
    main()
