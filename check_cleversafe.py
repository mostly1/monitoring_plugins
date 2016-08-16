#!/usr/bin/env python
#This needs to be cleaned up and commented before using



import os
import requests
import json
import math
import argparse

#requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description ='Icinga2 plugin to monitor cleversafe servers and services using their API', usage='use "%(prog)s --help" for more information', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-H', action="store", dest="host", help="ip address or hostname", required=True)
parser.add_argument('-c', action="store", dest="command", help='''Use one of the following commands at a time. At least one is required.
    check_dsnetMd     check dsnet MD process
    check_dsnetCore   check dsnet core process
    check_cron        check if cron process is running
    check_ssh         check if ssh process is running 
    check_ntp         check if ntp process is running
    check_load        check load averages
    check_memory      check memory available (in GBs)
    check_temp        check CPU temperatures''', required=True)
args = parser.parse_args()
host = args.host
command = args.command

#get raw json data from API
url = "http://"+host+":8192/state"
url2 = "http://"+host+":8192/statistic"

r = requests.get(url, verify=False)
s = requests.get(url2, verify=False)

data = json.loads(r.text)
data2 = json.loads(s.text)

#strip info we need for checks
cron = data["process"]["cron"]["status"]
dsnetCore = data["process"]["dsnet-core"]["status"]
dsnetMd = data["process"]["dsnet-md"]["status"]
ntp = data["process"]["ntp"]["status"]
ssh = data["process"]["ssh"]["status"]
load0 = data2["load"]
load1 = data2["loadX"]["average1"]
load5 = data2["loadX"]["average5"]
load15 = data2["loadX"]["average15"]
memTotalRaw = data2["memory"]["MemTotal"]
memAvailableRaw = data2["memory"]["MemAvailable"]


def plugin_out(status, string):
    if status == 2:
        print 'CRITICAL - '+string+' | {0}' .format(string)
        exit(2)
    elif status == 1:
        print 'WARNING - '+string+' |  {0}' .format(string)
        exit(1) 
    elif status == 0: 
        print 'OK - '+string+' | {0}' .format(string)
        exit(0)
    else:
        print "UNKNOWN - Check plugin output manually.."
        exit(3)
    

#this function is a work in progress but it does work......
def check_temp():
    warn=75
    crit=85
    count = 0
    #count how manu CPUS by counting the names
    for cpu_name in data2["cpuTemp"]:
        count +=1
    #if more than one, we compare both and warn based on first failure.
    if count > 1:
        cpu0 = data2["cpuTemp"]["CPU 0"]["temperature"] 
        cpu1 = data2["cpuTemp"]["CPU 1"]["temperature"]


        if cpu1 >= crit:
            status = 2
            string = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string)
        elif cpu1>= warn:
            status = 1
            string = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string)
        elif cpu0 >= crit:
            status = 2
            string = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string)
        elif cpu0 >= warn:
            status = 1
            string = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string)
        else:
            status = 0
            string = "cpu0="+str(cpu0)+" cpu1="+str(cpu1)
            plugin_out(status, string)


#single CPU
    else:
        cpu0 = data2["cpuTemp"]["CPU 0"]["temperature"]
        if cpu0 >= crit:
            status = 2
            string = "cpu0="+str(cpu0)
            plugin_out(status, string) 
        elif cpu0 >= warn:
            status = 1
            string = "cpu0="+str(cpu0)
            plugin_out(status, string)
        else:
            status = 0
            string = "cpu0="+str(cpu0)
            plugin_out(status, string)
    

#check if Cron process is running
def check_cron():
    if cron == "OK":
        string = "Cron process is running.."
        status = 0
        plugin_out(status, string)
    else:
        string = "Cron process is not runnning.."
        status = 2
        plugin_out(status, string)

#check if dsnetCore process running
def check_dsnetCore():
    if dsnetCore == "OK":
        string = "dsnetCore process is running.."
        status = 0 
        plugin_out(status, string)
    else:
        string = "dsnetCore process is not running.."
        status = 2
        plugin_out(status, string)

# check if dsnetMd is running
def check_dsnetMd():
    if dsnetMd == "OK":
        string = "dsnetMd process is running.."
        status = 0 
        plugin_out(status, string)
    else:
        string = "dsnetMd process is not running.."
        status = 2
        plugin_out(status, string)

#check if ntp is running
def check_ntp():
    if ntp == "OK":
        string = "ntp process is running.."
        status = 0
        plugin_out(status, string)
    else:
        string = "ntp process is not running.."
        status = 2
        plugin_out(status, string)

#check if ssh is running..
def check_ssh():
    if ssh == "OK":
        string = "ssh process is running.."
        status = 0 
        plugin_out(status, string)
    else:
        string = "ssh process is not running.."
        status = 2 
        plugin_out(status, string)

#check load averages..
def check_load():
    warn=750
    crit=1200
    if load0 >= crit:
        string = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 2 
        plugin_out(status, string)
    elif load0 >= warn:
        string = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 1 
        plugin_out(status, string) 
    else:
        string = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 0
        plugin_out(status, string)

#check memory available
def check_memory():
    warn=10
    crit=5
    memTotal = memTotalRaw / (1024**3)
    memAvailable = memAvailableRaw / (1024**3) 
    if memAvailable <= crit:
        string = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 2
        plugin_out(status, string)
    elif memAvailable <= warn:
        string = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 1
        plugin_out(status, string)
    else: 
        string = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 0 
        plugin_out(status, string)

#hostalive check / ping 
def check_ping():
    response = os.system("ping -c 1 " + host)
    if response == 0:
        string = "Ping Success"
        status = 0 
        plugin_out(status, string)

    else:
        string = "Ping error"
        status = 2
        plugin_out(status, string)


#makeshift case statement because python doesnt believe in switch/case 
def run_command(command):
    if command == "check_cron":
        check_cron()
    elif command == "check_dsnetCore":
        check_dsnetCore()
    elif command == "check_dsnetMd":
        check_dsnetMd()
    elif command == "check_ntp":
        check_ntp()
    elif command == "check_ssh": 
        check_ssh()
    elif command == "check_load":
        check_load()
    elif command == "check_memory":
        check_memory()
    elif command == "check_ping":
        check_ping()
    elif command == "check_temp":
        check_temp()
    else:
        print "Seems like you selected an invalid option, please try ./check_cleversafe.py --help for options.."
        exit(2)


#main function
run_command(command)
