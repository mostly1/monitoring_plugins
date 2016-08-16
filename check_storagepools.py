#!/usr/bin/env python
#plugin to check storage pool utilization using cleversafe API
#version 1.0
#J. Mazzone




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
parser.add_argument('-p', action="store", dest="pool", type=str, help="name of storage pool. Get from Manager..")
args = parser.parse_args()
host = args.host
pool_name = args.pool

url = "https://"+host+"/manager/api/json/1.0/listStoragePools.adm"

r = requests.get(url, verify=False, auth=(username,password))
#print(r.text)
data = json.loads(r.text)

pools_dict = {}
storagePools = data["responseData"]["storagePools"]
keys_to_include = ['capacity', 'utilization']
for pool in storagePools:
    pools_dict[pool['name']] = {}
    for key in keys_to_include:
        pools_dict[pool['name']][key] = pool[key]

cap = pools_dict[pool_name]['capacity']
used = pools_dict[pool_name]['utilization']
remaining = cap - used
total = float(remaining) / float(1099511627776)
#print total

if total < float(50.0):
    print "{} has {} TiB remaining in storage pool" .format(pool_name, round(total,2))
    exit(2)
    if total < float(75.0):
        print "{} has {} TiB remaining in storage pool" .format(pool_name, round(total,2))
        exit(1)

print "{} has {} TiB remaining in storage pool" .format(pool_name, round(total,2))
exit(0)


