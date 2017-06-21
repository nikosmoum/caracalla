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

'''
This script is used to create supporting csvs for each jmx test.
The script requires a config json with an array of csvs where configuration of each csv is of the format:
{
 "name": "csv_file_name",
 "projection": "fields_to_return as column_name_for_csv",
 "from": "table_names_with_aliases",
 "selection": "where_clauses",
 "owner_id_column": "owner_id_column"
}

Currently it ensures no overlap in owners between any of the csvs or between any record within a csv.
'''

import logging
import json
import MySQLdb
import psycopg2

from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger('generate-csv')


def parse_options():
    usage = "%(prog)s [options] config_file"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-l", "--limit",
                        dest="limit",
                        default=10,
                        help="The number of rows to return")
    parser.add_argument("--host",
                        dest="host",
                        default="localhost",
                        help="The mysql hostname")
    parser.add_argument("-u", "--username",
                        dest="username",
                        default="candlepin",
                        help="The username for the database")
    parser.add_argument("-p", "--password",
                        dest="password",
                        default="",
                        help="The password for the database user")
    parser.add_argument("-n", "--database-name",
                        dest="database",
                        default="candlepin",
                        help="The database name")
    parser.add_argument("-t", "--database-type",
                        dest="type",
                        choices=["mysql","postgres"],
                        default="mysql",
                        help="The database type")

    (options, args) = parser.parse_known_args()
    if len(args) != 1:
        parser.error("You must provide a config file name with sql")
    return (options, args)

def get_connection(options):
    if options.type == 'mysql':
        return MySQLdb.connect(options.host, options.username, options.password, options.database)
    elif options.type == 'postgres':
        return psycopg2.connect(host=options.host, database=options.database, user=options.username, password=options.password)
    else:
        raise TypeError('Unsupported database type: %s' % options.type)

def main():
    (options, args) = parse_options()
    input_file = args[0]
    logger.debug("Opening %s" % input_file)
    csvs = json.load(open(input_file))['csvs']
    conn = get_connection(options)
    cursor = conn.cursor()
    owner_ids = ["'0'"]
    for csv in csvs:
        file_name = csv['name']
        owner_id_column = csv['owner_id_column']
        f = open(file_name, 'w+')
        query = "select " + csv['projection'] + ", " + owner_id_column + \
                " from " + csv['from'] + \
                " where "
        if 'selection' in csv:
            query += csv['selection'] + " and "
        # split up owner ids into batches of 999
        owner_id_batches = [owner_ids[i:i + 999] for i in xrange(0, len(owner_ids), 999)]
        for i, owner_id_batch in enumerate(owner_id_batches):
            if i != 0:
                query += " and "
            query += owner_id_column + " not in (" + ",".join(owner_id_batch) + ")"
        if 'group' in csv:
            query += ' group by ' + csv['group']
        if 'limit' in csv:
            limit = csv['limit']
        else:
            limit = str(options.limit)
        query += " limit " + limit
        print "Writing file : %s ...." % file_name
        cursor.execute(query)
        fields = ','.join([i[0] for i in cursor.description])
        f.write(fields + "\n")
        rows = cursor.fetchall()
        for row in rows:
            owner_ids.append("'" + str(row[-1]) + "'")
            f.write(','.join(row) + "\n")
        f.close()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
