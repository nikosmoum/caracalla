#!/usr/bin/env python

import logging
import csv

from optparse import OptionParser

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger('parse-jtl')


def parse_options():
    usage = "usage: %prog [options]  results_file"
    parser = OptionParser(usage=usage)
    parser.add_option("--pretty-print",
                      action="store_true",
                      dest="pretty_print",
                      help="parse and pretty print.")
    parser.add_option("-p", "--parse",
                      action="store_true",
                      dest="parse",
                      help="parse to compute a dictionary.")
    parser.add_option("-c", "--compare",
                      action="store_true",
                      dest="compare",
                      help="compare results with baseline dictionary")
    parser.add_option("-e", "--expected",
                      dest="expected",
                      help="success criteria dictionary, only used with -c")
    parser.add_option("-b", "--baseline",
                      dest="baseline",
                      help="dictionary to compare with, only used with -c")
    parser.add_option("-o", "--output",
                      dest="output",
                      help="output file to write the result to.")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("You must (only) provide a results file to parse/compare")
    if (options.parse is None and options.compare is None and
            options.pretty_print is None):
        parser.error("You must choose a command (-p, --pretty-print or -c)")
    compare_opts = options.baseline is not None or options.expected is not None
    if (compare_opts and options.compare is None or
            options.compare and (options.baseline is None or
                                 options.expected is None)):
        parser.error("-b and -e must be provided with -c")
    return (options, args)


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
                                  input_dict[key]['success_%'],
                                  deviance_dict[key]['required_success'])
        result += compare_average(key,
                                  input_dict[key]['average'],
                                  baseline_dict[key]['average'],
                                  deviance_dict[key]['allowed_deviance'])
    return result


def parse_csv(input_file):
    dict = {}
    with open(input_file, 'rb') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row[2] not in dict:
                dict[row[2]] = {'count': 0, 'elapsed': 0, 'success': 0}
            dict[row[2]]["count"] += 1
            dict[row[2]]["elapsed"] += int(row[1])
            if row[7] == "true":
                dict[row[2]]["success"] += 1
    for key, result in dict.items():
        dict[key]["success_%"] = (result["success"] * 100) / result["count"]
        dict[key]["average"] = (result["elapsed"]) / result["count"]
    return dict


def main():
    (options, args) = parse_options()
    input_file = args[0]
    logger.debug("Opening %s" % input_file)
    dict = parse_csv(input_file)
    output_txt = None
    successful_compare = False

    if options.parse:
        output_txt = dict
    elif options.pretty_print:
        output_txt = "success %, average time elapsed, API\n"
        for key, result in sorted(dict.items()):
            output_txt += "%s, %s, %s \n" \
                % (result["success_%"], result["average"], key)
    else:
        baseline_txt = open(options.baseline, 'r').read()
        expected_txt = open(options.expected, 'r').read()
        output_txt = compare_csv(dict, eval(baseline_txt), eval(expected_txt))
        if not output_txt:
            successful_compare = True
            output_txt = "Successful compare!"

    if options.output is not None:
        output_file = open(options.output, 'w+')
        output_file.write(str(output_txt))
    elif not successful_compare:
        print output_txt
    if options.compare and not successful_compare:
        raise Exception(output_txt)


if __name__ == "__main__":
    main()
