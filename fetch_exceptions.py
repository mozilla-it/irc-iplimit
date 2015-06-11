#!/usr/bin/python

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


#JSON_URL="http://127.0.0.1:5000/json"
#EXISTING_EXCEPTIONS="/Users/dan/sysadmins/puppet/trunk/modules/inspircd/files/global/connect.conf"

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
    parser.add_option('--iplimit-url', dest="url", help='iplimit JSON URL (required)')
    parser.add_option('--existing-exceptions', dest='existing', help='Existing exceptions, in inspircd config format (required). Exceptions fetched via iplimit API are checked against this file and skipped if matched.')
    parser.add_option('--limit', dest='limit', default=100, help='Connection limit (default: 100)')
    parser.add_option('--out', dest="out", help="File to write inspircd config to (If omitted: stdout)")
    (options, args) = parser.parse_args()
    return options


def loadExistingExceptions(existing_file):
    fp = open(existing_file)
    existings = fp.read()
    quoted = re.compile(r'"(.*?)"')
    ips = []
    for line in existings.split('\n'):
        if 'main" allow="' in line:
            value = re.findall(quoted, line.split(" ")[2])[0]
            # in inspircd config, you can specify 192.168.0.* or 192.168.0.0/24
            # but python IP libraries only understand slash notiation
            # so we convert
            pass1 = re.sub(r'\*', '0/24', value)

            # if it ends in .0, add /24 (yes, I know this is kind of guessing)
            pass2 = re.sub(r'.0$', '.0/24', pass1)

            # if there is no /, assume it's a single IP, and add /32
            if '/' not in pass2:
                pass2 += '/32'

            ips.append(pass2)
    return ips

def exceptionExists(ip, existing_exceptions):
    for existing in existing_exceptions:
        try:
            #print "IP: %s, Network: %s" % (ip, existing)
            if IPAddress(ip) in IPNetwork(existing):
                return True
        except core.AddrFormatError:
            pass
    return False

def main():
    options = process_arguments()
    if not options.url:
        print "--iplimit-url is a required parameter. run with --help for details."
        return -1
    if not options.existing:
        print "--existing-exceptions is a required parameter. run with --help for details."
        return -1
    req = urllib2.urlopen(options.url)
    blob = req.read()
    exceptions = json.loads(blob)
    existing_exceptions = loadExistingExceptions(options.existing)
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
            print '<connect parent="main" allow="%s" localmax="%s" globalmax="%s" limit="%s" modes="+x">\n' % (ip, options.limit, options.limit, int(options.limit) + 1)

if __name__ == '__main__':
    main()
