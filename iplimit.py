#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# by Dan Parsons, aka lerxst, <dparsons@mozilla.com>

from flask import Flask
from flask import request
from flaskext.mysql import MySQL
from netaddr import IPNetwork, IPAddress, core
import time
import datetime
import json
import ConfigParser
import optparse
import sys
import os

# in days
DEFAULT_EXCEPTION_LENGTH=7

mysql = MySQL()
DFORMATTER = "%Y-%m-%d %H:%M:%S"
TIMEZONE = "GMT %s" % (0 - time.timezone / 60 / 60)

app = Flask(__name__)

IPLIMIT_PROTO="1.0"

mysql.init_app(app)

def load_config(config_file):
    if not os.path.exists(config_file):
        print "ERROR: Config file %s not found." % config_file
        sys.exit(-1)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    if 'global' not in config.sections():
        print "ERROR: [global] section not found in %s." % config_file
        sys.exit(-1)
    app.config['MYSQL_DATABASE_USER'] = config.get('global', 'mysql_user')
    app.config['MYSQL_DATABASE_PASSWORD'] = config.get('global', 'mysql_password')
    app.config['MYSQL_DATABASE_DB'] = config.get('global', 'mysql_database')
    app.config['MYSQL_DATABASE_HOST'] = config.get('global', 'mysql_server')

def validIP(ip):
    try:
        x = IPAddress(ip)
    except:
        return False
    return True

def process_arguments():
    parser = optparse.OptionParser(version="%prog 0.1")
    parser.set_usage("iplimit.py wsgi")
    parser.add_option('--config', dest='config', default='./iplimit.conf', help='Configuration file (required) (default: ./iplimit.conf)')
    parser.add_option('--debug', dest='debug', default=False, action="store_true", help="Enable Flask debug mode.")
    (options, args) = parser.parse_args()
    return options

@app.route('/')
def create_exception():
    # get source IP address. this may need to change depending on how the app is hosted
    ip = request.remote_addr

    # get requestor username from http auth
    remote_user = request.remote_user
    if validIP(ip) is False:
        return "Invalid IP address: %s" % (ip)

    conn = mysql.connect()
    cursor = conn.cursor()

    # does an exception for this address already exist?
    cursor.execute("""SELECT ExceptionIP, ExpirationDate FROM Exception WHERE ExceptionIP=%s""", (ip,))
    data = cursor.fetchone()
    if data is None:
        # this is a new exception
        creation = datetime.datetime.now()
        expiration = creation + datetime.timedelta(days=DEFAULT_EXCEPTION_LENGTH)
        cursor.execute("""INSERT INTO Exception (ExceptionIP, CreationDate, ExpirationDate, Requestor) VALUES (%s, %s, %s, %s)""",
            (ip, creation, expiration, remote_user))
        conn.commit()
        return "A new exception has been created for IP address %s. It will expire on %s %s. It will take effect within 1 minute." % (ip, expiration.strftime(DFORMATTER), TIMEZONE)
    else:
        # this is an existing exception, so update the expiration datetime
        existing_ip = data[0]
        original_expiration_date = data[1]
        if validIP(existing_ip) is False:
            return "Invalid IP address: %s" % (existing_ip)
        expiration = datetime.datetime.now() + datetime.timedelta(days=DEFAULT_EXCEPTION_LENGTH)
        cursor.execute("""UPDATE Exception SET ExpirationDate=%s, Requestor=%s WHERE ExceptionIP=%s""", (expiration, remote_user, ip,))
        conn.commit()
        return "Your existing exception for IP address %s has been updated to expire on %s %s. This change will take effect within 1 minute." % (ip, expiration.strftime(DFORMATTER), TIMEZONE)

@app.route('/json')
def dumpJSON():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM Exception WHERE ExpirationDate > NOW()""")
    rows = cursor.fetchall()
    exceptions = []
    exceptions.append({'iplimit_proto':IPLIMIT_PROTO})
    for row in rows:
        t = {}
        t["ExceptionIP"] = str(row[0])
        t["CreationDate"] = row[1].strftime(DFORMATTER)
        t["ExpirationDate"] = row[2].strftime(DFORMATTER)
        exceptions.append(t)
    return json.dumps(exceptions)

if __name__ == '__main__':
    options = process_arguments()
    if not options.config:
        print "--config is a required parameter."
        sys.exit(-1)
    load_config(options.config)
    if options.debug:
        print "Debug mode enabled!"
        app.debug = True
    app.run()
