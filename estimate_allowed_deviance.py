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
This script is used for computing deviance of performance results
from several existing results.
"""

from __future__ import print_function

import json
import argparse
from os import listdir, getcwd
from os.path import isfile, join


class DevianceEstimator(object):
    """
    Class for estimating deviance of performance results
    """

    def __init__(self, options):
        self.options = vars(options)
        self.perf_test_results = {}
        self.success_rates = {}
        self.estimations = {}

    def _add_perf_test_result(self, filename):
        """
        Add result of perf test result to dictionary of results
        :param filename: filename with perf test result
        :return: None
        """
        with open(filename, 'r') as perf_res_file:
            try:
                perf_test_result = json.load(perf_res_file)
            except ValueError:
                pass
                # print('Loading file: %s [FAILED]' % filename)
            else:
                self.perf_test_results[filename] = perf_test_result
                # print('Loading file: %s [DONE]' % filename)

    def _read_resutls(self):
        """
        Try to load all json files with performance tests from directory
        :return: None
        """
        path = self.options['directory']
        if path is None:
            path = getcwd()
        file_list = [path + f for f in listdir(path) if isfile(join(path, f))]
        for filename in file_list:
            self._add_perf_test_result(filename)

    def _estimate_deviances(self):
        """
        Compute deviations from loaded data
        :return: None
        """
        for result in self.perf_test_results.values():
            for api_call, api_call_result in result.items():
                # print(api_call, api_call_result)
                count = api_call_result['count']
                success = api_call_result['success']
                success_rate = float(success) / float(count)
                api_call_results = self.success_rates.setdefault(api_call, [])
                api_call_results.append(success_rate)

        for api_call, success_rates in self.success_rates.items():
            # Compute average success rate
            avg_suc_rate = float(sum(success_rates)) / len(success_rates)
            # Compute maximal deviation of success rate
            max_dev = max(map(lambda suc_rate: abs(avg_suc_rate - suc_rate), success_rates))
            # Save values in percents
            self.estimations[api_call] = {
                'required_success': 100.0 * avg_suc_rate - 5.0,
                'allowed_deviance': 100.0 * max_dev + 5.0
            }

    def _write_results(self):
        """
        Write new file with expected deviations
        :return: None
        """
        output_file = self.options['output']
        output_text = json.dumps(self.estimations, indent=2)
        if output_file is None:
            print(output_text)
        else:
            with open(output_file, 'w') as json_file:
                json_file.write(output_text)

    def perform(self):
        """
        Perform all necessary action to estimate new expected deviations
        :return: None
        """
        self._read_resutls()
        self._estimate_deviances()
        self._write_results()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory',
                        action='store', dest='directory',
                        default=None,
                        help='Folder with results of performance tests')
    parser.add_argument('-o', '--output',
                        action='store', dest='output',
                        default=None,
                        help='Output json file with expected deviances')
    options = parser.parse_args()

    deviance_estimator = DevianceEstimator(options)
    deviance_estimator.perform()


if __name__ == '__main__':
    main()
