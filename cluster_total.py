#!/usr/bin/env python

import requests
import json
import math
import argparse

#requests.packages.urllib3.disable_warnings()

with open('creds.json') as cred_file:
    auth = json.load(cred_file)

username = auth['creds']['username']
password = auth['creds']['password']



parser  = argparse.ArgumentParser(add_help=True)
parser.add_argument('-H', action="store", dest="host", help="ip address or hostname of manager", required=True)
args = parser.parse_args()
host = args.host



url = "https://"+host+"/manager/api/json/1.0/dsnetComplianceReport.adm"

r = requests.get(url, verify=False, auth=(username,password))
#print(r.text)
data = json.loads(r.text)
cap = data["responseData"]["dsNetComplianceReport"]["dsNetStorageSummary"]['dsNetCapacity']
used = data["responseData"]["dsNetComplianceReport"]["dsNetStorageSummary"]['dsNetUtilization']
remaining = cap - used
total = float(remaining) / float(1099511627776)
  
if total < float(150.0):
    print "{} TiB remaining in cluster..." .format(round(total,2))
    exit(1)
    if total < float(100.0):
        print "{} TiB remaining in cluster..." .format(round(total,2))
        exit(2)


print "{} TiB remaining in cluster" .format(round(total,2))
exit(0)
