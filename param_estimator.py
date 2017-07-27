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
This script is used for estimating deviance and baseline of performance
results from several existing results. Computed values are stored in
configuration files. These values are used as parameters in next
performance tests.
"""

from __future__ import print_function

import json
import argparse
import os


class Estimator(object):
    """
    Class for estimating deviance and baseline of performance results
    """

    def __init__(self, options):
        # Command line options
        self.options = options
        # All results of all loaded performance tests
        self.perf_test_results = {}
        # Success rates of particular tests
        self.success_rates = {}
        # Average elapsed times of particular tests
        self.avg_elapsed_times = {}
        # Computed estimations for partucalar tests
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

    def _read_results(self):
        """
        Try to load all json files with performance tests from directory
        :return: None
        """
        path = self.options.directory
        if path is None:
            path = os.getcwd() + os.path.sep
        file_list = [path + f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        for filename in file_list:
            self._add_perf_test_result(filename)

    def _estimate(self):
        """
        Compute estimation
        :return: None
        """
        # if-elif-elif-elif-else is for newbies ;-)
        {
            'deviances': self._estimate_deviances,
            'baseline': self._estimate_baseline
        }[self.options.type]()

    def _gather_required_data(self):
        """
        Gather required data for estimation
        """
        for result in self.perf_test_results.values():
            for api_call, api_call_result in result.items():
                # print(api_call, api_call_result)
                # Get average elapsed time of the performance test
                avg_elapsed_time = api_call_result['average']
                # Number of iteration of the performance test
                count = api_call_result['count']
                # Number of success iterations
                success = api_call_result['success']
                # Do not use value from file, because it is rounded. Compute it.
                success_rate = float(success) / float(count)
                # Append results to lists
                api_call_suc_rates = self.success_rates.setdefault(api_call, [])
                api_call_suc_rates.append(success_rate)
                api_call_avg_elap_time = self.avg_elapsed_times.setdefault(api_call, [])
                api_call_avg_elap_time.append(avg_elapsed_time)

    def _compute_avg_elap_time(self, api_call):
        """Compute average elapsed time for given API call"""
        elapsed_times = self.avg_elapsed_times[api_call]
        return float(sum(elapsed_times)) / len(elapsed_times)

    def _compute_avg_success_rate(self, api_call):
        """"Compute average success rate for given API call"""
        success_rates = self.success_rates[api_call]
        return float(sum(success_rates)) / len(success_rates)

    def _estimate_baseline(self):
        """
        Compute estimation of baseline
        :return: None
        """
        self._gather_required_data()

        for api_call in self.success_rates.keys():
            # Compute average success rate
            avg_suc_rate = self._compute_avg_success_rate(api_call)

            # Compute average elapsed time
            avg_elapsed_time = self._compute_avg_elap_time(api_call)

            # Save values
            self.estimations[api_call] = {
                'average': round(avg_elapsed_time + 5.0, 2),
                'success_%': round(100.0 * avg_suc_rate - 5.0, 2),
            }

    def _estimate_deviances(self):
        """
        Compute deviations from loaded data
        :return: None
        """
        self._gather_required_data()

        for api_call in self.success_rates.keys():
            # Compute average success rate
            avg_suc_rate = self._compute_avg_success_rate(api_call)

            # Compute average elapsed time
            avg_elapsed_time = self._compute_avg_elap_time(api_call)

            # Compute maximal difference of elapsed times
            elapsed_times = self.avg_elapsed_times[api_call]
            max_dev = max(map(lambda elap_time: abs(avg_elapsed_time - elap_time) / elap_time, elapsed_times))

            # Save values in percents (multiplication by 100.0)
            self.estimations[api_call] = {
                'required_success': round(100.0 * avg_suc_rate - 5.0, 2),
                'allowed_deviance': round(100.0 * max_dev + 5.0, 2)
            }

    def _write_results(self):
        """
        Write new file with expected deviations
        :return: None
        """
        output_file = self.options.output
        output_text = json.dumps(self.estimations, indent=4, sort_keys=True)
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
        self._read_results()
        self._estimate()
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
    parser.add_argument('-t', '--type',
                        choices=['deviances', 'baseline'], dest='type',
                        default='deviances',
                        help='Type of estimation to compute (default: deviances).')
    options = parser.parse_args()

    deviance_estimator = Estimator(options)
    deviance_estimator.perform()


if __name__ == '__main__':
    main()
