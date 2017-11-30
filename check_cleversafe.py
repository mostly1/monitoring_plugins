#!/usr/bin/env python
#This needs to be cleaned up and commented before using



import os
import requests
import json
import math
import argparse
import subprocess

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
    check_temp        check CPU temperatures
    get_serial_num    pulls serial number from host
    check_disk_temp   calculates average of all disk temps in system
    check_disk_health checks the health and number of disks as reported to the manager GUI''', required=True)

args = parser.parse_args()
host = args.host
command = args.command

#get raw json data from API
url = "http://"+host+":8192/state"
url2 = "http://"+host+":8192/statistic"

#Not sure if this was the right way to do this but it works.
#Hostalive checks via the ping function would not work due to "requests" being called internally
#added this internal check before the requests call so anything that requests it will get exit(2).
#dirty but it works.

def hostalive(host):
    try:
        output = subprocess.check_output("ping -c 2 "+host, shell=True)
    except Exception, e:
        return False

    return True

if hostalive(host) == False:
    print "CRITICAL - Timeout! Cannot Ping Device"
    exit(2)

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
serialNumber= data2["serial"]
uptime= data2["uptime"]
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



def check_fan_speed():
    num_fans = 0
    fan_speed_total = 0
    status = 0
    for fan_id in data2["fan"]:
        num_fans += 1
        fan_speed_total += data2["fan"][fan_id]["speed"]
    avg_fan_speed = fan_speed_total / num_fans
    string = "Current average fan speed: "+str(avg_fan_speed)+" Total Fans: "+str(num_fans)
    plugin_out(status, string)


def check_disk_health():
    num_disks = 0
    disk_state = []
    expected_num_disks = 49
    status = 1
    string = "Something went wrong. Run plugin manually..."
    for disk_id in data2["diskHealth"]:
	num_disks += 1
        disk_state =  data2["diskHealth"][disk_id]["status"]
        if disk_state != "ONLINE":
            status = 2
            string = "One or more disks are not in good health."
            break
	else:
            status = 0
            string = "Disk health is ok."
    if num_disks < expected_num_disks:
        status = 2
        string = "Number of disks is less than expected.( "+str(num_disks)+" ) Check GUI."
    plugin_out(status, string)

def check_disk_temp():
    disk_temp_total = 0
    num_disks = 0
    warn = 53
    crit = 60
    for disk_id in data2["diskHealth"]:
        disk_temp_total += data2["diskHealth"][disk_id]["temperature"]
        num_disks += 1
    avg_disk_temp = disk_temp_total / num_disks
    if avg_disk_temp >= crit:
        status = 2
        string = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string)
    elif avg_disk_temp >= warn:
        status = 1
        string = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string)
    else:
        status = 0
	string = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string)

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
    warn=2500
    crit=3500
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


def get_serial_num():
    print host+" "+serialNumber

def check_psu():
    status = 0
    for psu in data2["psu"]:
        health=data2["psu"][psu]["healthy"]
        psu_name=data2["psu"][psu]["name"]
        if str(health) == "False":
            status = 2
            break
    if status != 0:
        string = "Power supply has failed. PSU Name is: "+psu_name+" Check GUI.."
        plugin_out(status, string)
    else:
        string = "Power supplies OK.."
        plugin_out(status, string)

#check uptime if system flaps and hostalive doesnt catch it.
#Unlikely with a storage server but you never know.
def check_uptime():
    status = 0
    hours_in_seconds = 4320000
    if uptime < hours_in_seconds:
        status = 2
        string = "Uptime="+str(uptime)
    else:
        string = "Uptime="+str(uptime)
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
    elif command == "get_serial_num":
        get_serial_num()
    elif command == "check_disk_temp":
        check_disk_temp()
    elif command == "check_disk_health":
        check_disk_health()
    elif command == "check_fan_speed":
        check_fan_speed()
    elif command == "check_psu":
        check_psu()
    elif command == "check_uptime":
        check_uptime()
    else:
        print "Seems like you selected an invalid option, please try ./check_cleversafe.py --help for options.."
        exit(2)


#main function
run_command(command)
