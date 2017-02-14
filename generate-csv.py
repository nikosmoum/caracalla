#!/usr/bin/env python

import logging
import json
import MySQLdb
import psycopg2

from optparse import OptionParser

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger('generate-csv')

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
#TODO: add postgre support

def parse_options():
    usage = "usage: %prog [options] config_file"
    parser = OptionParser(usage=usage)
    parser.add_option("-l", "--limit",
                      dest="limit",
                      default=10,
                      help="the number of rows to return")
    parser.add_option("--host",
                      dest="host",
                      default="localhost",
                      help="the mysql hostname")
    parser.add_option("-u", "--username",
                      dest="username",
                      default="candlepin",
                      help="the username for the database")
    parser.add_option("-p", "--password",
                      dest="password",
                      default="",
                      help="the password for the database user")
    parser.add_option("-n", "--database-name",
                      dest="database",
                      default="candlepin",
                      help="the database name")
    parser.add_option("-t", "--database-type",
                      type="choice",
                      dest="type",
                      choices=["mysql","postgres"],
                      default="mysql",
                      help="the database type")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("You must provide a config file name with sql")
    return (options, args)

def get_connection(options):
    if options.type == 'mysql':
        return MySQLdb.connect(options.host, options.username, options.password, options.database)
    else:
        return psycopg2.connect(host=options.host, database=options.database, user=options.username, password=options.password)

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
