#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# by Dan Parsons, aka lerxst, <dparsons@mozilla.com>

# This script does several things:
# (1) Fetches the list of self-service exceptions from iplimit.irc.mozilla.org
# (2) Loads the current list of regular, stored-in-puppet exceptions from inspircd's config files
# (3) For every IP address returned from iplimit.irc.mozilla.org:
#     (a) Is this IP address already excepted elsewhere in inspircd's config? if so, skip it
#     (b) Is this IP address already excepted by way of a CIDR that already exists in inspircd's config? if so, skip it
#     (c) Unless a self-service IP has been skipped by (a) or (b), write inspircd config for it.

import urllib2
import json
import re
from netaddr import IPNetwork, IPAddress, core
import datetime
import optparse
import ConfigParser
import os
import base64

IPLIMIT_PROTO="1.0"

_config = {}

def load_config(config_file):
    global _config
    if not os.path.exists(config_file):
        print "ERROR: Config file %s not found." % config_file
        sys.exit(-1)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    if 'global' not in config.sections():
        print "ERROR: [global] section not found in %s." % config_file
        sys.exit(-1)
    _config = config

def process_arguments():
    usage = """%prog v0.1
    This script does several things:
    (1) Fetches the list of self-service exceptions from iplimit.irc.mozilla.org
    (2) Loads the current list of regular, stored-in-puppet exceptions from inspircd's config files
    (3) For every IP address returned from iplimit.irc.mozilla.org:
         (a) Is this IP address already excepted elsewhere in inspircd's config? if so, skip it
         (b) Is this IP address already excepted by way of a CIDR that already exists in inspircd's config? if so, skip it
         (c) Unless a self-service IP has been skipped by (a) or (b), write inspircd config for it.
    """
    parser = optparse.OptionParser(version="%prog 0.1")
    parser.set_usage(usage)
    parser.add_option('-f', dest="config_file", help="config file (required)")
    (options, args) = parser.parse_args()
    return options


def loadExistingExceptions(existing_file):
    fp = open(existing_file)
    existings = fp.read()
    quoted = re.compile(r'"(.*?)"')
    ips = []
    for line in existings.split('\n'):
        if ('main" allow="' in line) and (':' not in line): # if it has a :, it's ipv6, ignore it, this app doesn't support ipv6
            value = re.findall(quoted, line.split(" ")[2])[0]
            # in inspircd config, you can specify 192.168.0.* or 192.168.0.0/24
            # but python IP libraries only understand slash notiation
            # so we convert
            pass1 = re.sub(r'\*', '0/24', value)

            # if it ends in .0, add /24 (yes, I know this is kind of guessing)
            pass2 = re.sub(r'\.0$', '.0/24', pass1)

            # if there is no /, assume it's a single IP, and add /32
            if '/' not in pass2:
                pass2 += '/32'

            ips.append(pass2)
    return ips

def exceptionExists(ip, existing_exceptions):
    for existing in existing_exceptions:
        try:
            if IPAddress(ip) in IPNetwork(existing):
                return True
        except core.AddrFormatError:
            pass
    return False

def main():
    options = process_arguments()
    if not options.config_file:
        print "-f is a required parameter. run with --help for details."
        return -1
    load_config(options.config_file)

    request = urllib2.Request(_config.get('global', 'iplimiturl'))
    user = _config.get('global', 'http_username')
    passwd = _config.get('global', 'http_password')
    b64str = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % b64str)

    req = urllib2.urlopen(request)
    blob = req.read()
    try:
        version = json.loads(blob)[:1][0]['iplimit_proto']
    except:
        print "Protocol mismatch with server. (iplimit_proto not found)"
        return -1
    if IPLIMIT_PROTO != version:
        print "Protocol mismatch with server. (%s != %s)" % (IPLIMIT_PROTO, version)
        return -1
    exceptions = json.loads(blob)[1:]
    existing_exceptions = loadExistingExceptions(_config.get('global', 'existing_exceptions'))
    for exception in exceptions:
        try:
            ip = IPAddress(exception["ExceptionIP"])
        except core.AddrFormatError:
            print "%s is not a valid IP. Terminating." % (exception["ExceptionIP"])
            return -1
        creation = datetime.datetime.strptime(exception["CreationDate"], '%Y-%m-%d %H:%M:%S')
        expiration = datetime.datetime.strptime(exception["ExpirationDate"], '%Y-%m-%d %H:%M:%S')
        # Does this exception already exist elsewhere in inspircd's config? If so, skip it
        if not exceptionExists(exception["ExceptionIP"], existing_exceptions):
            print "# iplimit.irc.mozilla.org exception. Created: %s. Expires: %s." % (creation, expiration)
            limit = _config.get('global', 'limit')
            print '<connect parent="main" allow="%s" localmax="%s" globalmax="%s" limit="%s" modes="+x">\n' % \
                (ip, limit, limit, int(limit) + 1)

if __name__ == '__main__':
    main()
