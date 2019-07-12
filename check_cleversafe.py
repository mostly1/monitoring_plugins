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
    check_disk_health checks the health and number of disks as reported to the manager GUI
    check_uptime      checks the uptime of the system
    check_psu         checks the health of the PSU
    check_fans        checks the health of the fans
    check_fan_speed   checks the average speed of the fans in the system''', required=True)

args = parser.parse_args()
host = args.host
command = args.command

#get raw json data from API
url = "http://"+host+":8192/state"
url2 = "http://"+host+":8192/statistic"


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

def plugin_out(status, string, perfdata):
    if status == 2:
        print 'CRITICAL - '+string+' | {0}' .format(perfdata)
        exit(2)
    elif status == 1:
        print 'WARNING - '+string+' |  {0}' .format(perfdata)
        exit(1)
    elif status == 0:
        print 'OK - '+string+' | {0}' .format(perfdata)
        exit(0)
    else:
        print "UNKNOWN - Check plugin output manually.."
        exit(3)



def check_fan_speed():
    num_fans = 0
    fan_speed_total = 0
    status = 0
    for fan_id in data2["chassis"][0]["fans"]:
        num_fans += 1
        fan_speed_total += fan_id["speed"]
    avg_fan_speed = fan_speed_total / num_fans
    string = "Average Fan Speed: "+str(avg_fan_speed)
    perfdata = "Average_fan_speed="+str(avg_fan_speed)+"; Total_Fans="+str(num_fans)
    plugin_out(status, string, perfdata)

def check_fans():
    status = 0
    for fan_id in data2["chassis"][0]["fans"]:
        if fan_id["status"] != "OK":
            string = "One or more fans are in poor health. Check GUI!"
            perfdata = "Fan_status=0"
            status = 2
            break
        elif fan_id["speed"] == 0:
            string = "One or more fans are in poor health. Check GUI!"
            perfdata = "Fan_status=0"
            status = 2
            break
        else:
            string = "All fans running and healthy"
            perfdata = "Fan_status=1"
    plugin_out(status, string, perfdata)


def check_disk_health():
    num_disks = 0
    disk_state = []
    expected_num_disks = 49
    status = 1
    string = "Something went wrong. Run plugin manually..."
    perfdata = "Disk_Health=-1"
    for disk_id in data2["diskHealth"]:
	num_disks += 1
        disk_state =  data2["diskHealth"][disk_id]["status"]
        if disk_state != "ONLINE":
            status = 2
            string = "One or more disks are not in good health."
            perfdata = "Dish_Health=0"
            break
	else:
            status = 0
            string = "Disk health is ok."
            perfdata = "Disk_Health=1"
    if num_disks < expected_num_disks:
        status = 2
        string = "Number of disks is less than expected.( "+str(num_disks)+" ) Check GUI."
        perfdata = "Disk_health=0"
    plugin_out(status, string, perfdata)

def check_disk_temp():
    disk_temp_total = 0
    num_disks = 0
    warn = 55
    crit = 60
    for disk_id in data2["diskHealth"]:
        disk_temp_total += data2["diskHealth"][disk_id]["temperature"]
        num_disks += 1
    avg_disk_temp = disk_temp_total / num_disks
    if avg_disk_temp >= crit:
        status = 2
        string = "Average Disk Temp: "+str(avg_disk_temp)
        perfdata = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string, perfdata)
    elif avg_disk_temp >= warn:
        status = 1
        string = "Average Disk Temp: "+str(avg_disk_temp)
        perfdata = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string, perfdata)
    else:
        status = 0
	string = "Average Disk Temp: "+str(avg_disk_temp)
        perfdata = "Average_disk_temp="+str(avg_disk_temp)
        plugin_out(status, string, perfdata)

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
            string = "CPU 0 Temp: "+str(cpu0)+"CPU 1 Temp: "+str(cpu1)
            perfdata = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string, perfdata)
        elif cpu1>= warn:
            status = 1
            string = "CPU 0 Temp: "+str(cpu0)+"CPU 1 Temp: "+str(cpu1)
            perfdata = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string, perfdata)
        elif cpu0 >= crit:
            status = 2
            string = "CPU 0 Temp: "+str(cpu0)+"CPU 1 Temp: "+str(cpu1)
            perfdata = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string, perfdata)
        elif cpu0 >= warn:
            status = 1
            string = "CPU 0 Temp: "+str(cpu0)+"CPU 1 Temp: "+str(cpu1)
            perfdata = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string, perfdata)
        else:
            status = 0
            string = "CPU 0 Temp: "+str(cpu0)+"CPU 1 Temp: "+str(cpu1)
            perfdata = "cpu0="+str(cpu0)+"; cpu1="+str(cpu1)
            plugin_out(status, string, perfdata)


#single CPU
    else:
        cpu0 = data2["cpuTemp"]["CPU 0"]["temperature"]
        if cpu0 >= crit:
            status = 2
            string = "CPU 0 Temp: "+str(cpu0)
            perfdata = "cpu0="+str(cpu0)
            plugin_out(status, string, perfdata)
        elif cpu0 >= warn:
            status = 1
            string = "CPU 0 Temp: "+str(cpu0)
            perfdata = "cpu0="+str(cpu0)
            plugin_out(status, string, perfdata)
        else:
            status = 0
            string = "CPU 0 Temp: "+str(cpu0)
            perfdata = "cpu0="+str(cpu0)
            plugin_out(status, string, perfdata)


#check if Cron process is running
def check_cron():
    cron = data["process"]["cron"]["status"]
    if cron == "OK":
        string = "Cron process is running. "
        perfdata = "Cron=1"
        status = 0
        plugin_out(status, string, perfdata)
    else:
        string = "Cron process is not running. "
        perfdata = "Cron=0"
        status = 2
        plugin_out(status, string, perfdata)

#check if dsnetCore process running
def check_dsnetCore():
    dsnetCore = data["process"]["dsnet-core"]["status"]
    if dsnetCore == "OK":
        string = "dsnetCore process is running."
        perfdata = "dsnetCore=1"
        status = 0
        plugin_out(status, string, perfdata)
    else:
        string = "dsnetCore process is not running."
        perfdata = "dsnetCore=0"
        status = 2
        plugin_out(status, string, perfdata)

# check if dsnetMd is running
def check_dsnetMd():
    dsnetMd = data["process"]["dsnet-md"]["status"]
    if dsnetMd == "OK":
        string = "dsnetMd process is running"
        perfdata = "dsnetMd=1"
        status = 0
        plugin_out(status, string, perfdata)
    else:
        string = "dsnetMd process is not running."
        perfdata = "dsnetMd=0"
        status = 2
        plugin_out(status, string, perfdata)

#check if ntp is running
def check_ntp():
    ntp = data["process"]["ntp"]["status"]
    if ntp == "OK":
        string = "ntp process is running."
        perfdata = "ntp=1"
        status = 0
        plugin_out(status, string, perfdata)
    else:
        string = "ntp process is not running."
        perfdata = "ntp=0"
        status = 2
        plugin_out(status, string, perfdata)

#check if ssh is running..
def check_ssh():
    ssh = data["process"]["ssh"]["status"]
    if ssh == "OK":
        string = "ssh process is running."
        perfdata = "ssh=1"
        status = 0
        plugin_out(status, string, perfdata)
    else:
        string = "ssh process is not running. "
        perfdata = "ssh=0"
        status = 2
        plugin_out(status, string, perfdata)

#check load averages..
def check_load():
    load0 = (data2["load"] / 100.0)
    load1 = (data2["loadX"]["average1"]/100.0)
    load5 = (data2["loadX"]["average5"]/100.0)
    load15 = (data2["loadX"]["average15"]/100.0)
    warn=250.0
    crit=350.0
    if load0 >= crit:
        string = "load 1: "+str(load1)+" Load 5: "+str(load5)+" Load 15: "+str(load15)
        perfdata = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 2
        plugin_out(status, string, perfdata)
    elif load0 >= warn:
        string = "load 1: "+str(load1)+" Load 5: "+str(load5)+" Load 15: "+str(load15)
        perfdata = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 1
        plugin_out(status, string, perfdata)
    else:
        string = "load 1: "+str(load1)+" Load 5: "+str(load5)+" Load 15: "+str(load15)
        perfdata = "load_1="+str(load1)+"; load_5="+str(load5)+"; load_15="+str(load15)
        status = 0
        plugin_out(status, string, perfdata)

#check memory available
def check_memory():
    warn=10
    crit=5
    memTotal = data2["memory"]["MemTotal"] / (1024**3)
    memAvailable = data2["memory"]["MemAvailable"] / (1024**3)
    if memAvailable <= crit:
        string = "Total Memory: "+str(memTotal)+"GB. Memory Available: "+str(memAvailable)+"GB."
        perfdata = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 2
        plugin_out(status, string, perfdata)
    elif memAvailable <= warn:
        string = "Total Memory: "+str(memTotal)+"GB. Memory Available: "+str(memAvailable)+"GB."
        perfdata = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 1
        plugin_out(status, string, perfdata)
    else:
        string = "Total Memory: "+str(memTotal)+"GB. Memory Available: "+str(memAvailable)+"GB."
        perfdata = "Total_Memory="+str(memTotal)+"; Memory_Available="+str(memAvailable)
        status = 0
        plugin_out(status, string, perfdata)





def check_ping(host):
    warn="10,2%"
    crit="20,5%"
    output = subprocess.Popen("/usr/lib/nagios/plugins/check_ping -H %s -w %s -c %s" % (str(host), str(warn), str(crit)), shell=True, stdout=subprocess.PIPE)
    for line in output.stdout.readlines():
        perfdata = line.strip().split('|')[-1]
    if output.wait() != 0:
        status = 2
        string = "Timeout! cannot ping device!"
        plugin_out(status, string, perfdata)
    else:
        status = 0
        string = "Host is alive!"
        plugin_out(status, string, perfdata)


#hostalive check / ping
#def check_ping():
#    response = os.system("ping -c 1 " + host)
#    if response == 0:
#        string = "Ping Success"
#        status = 0
#        plugin_out(status, string)
#
#    else:
#        string = "Ping error"
#        status = 2
#        plugin_out(status, string)

def get_serial_num():
    print host+" "+data2["serial"]

def check_psu():
    status = 0
    for psu in data2["chassis"][0]["powerSupplies"]:
        health=psu["status"]
        psu_name=psu["name"]
        if str(health) == "False":
            status = 2
            break
    if status != 0:
        string = "Power supply has failed. PSU Name is: "+psu_name+" Check GUI.."
        perfdata = "PSU_Status=0"
        plugin_out(status, string, perfdata)
    else:
        string = "Power supplies OK.."
        perfdata = "PSU_Status=1"
        plugin_out(status, string, perfdata)

#check uptime if system flaps and hostalive doesnt catch it.
#Unlikely with a storage server but you never know. uptime value is not seconds, microseconds, or nanoseconds.
#Had to multiply by .01 to get days value.
def check_uptime():
    uptime= data2["uptime"]
    status = 0
    hours_in_seconds = 43200
    hours = uptime / 86400
    days = hours * .01

    if uptime < hours_in_seconds:
        status = 2
        string = "Server uptime is : "+str(days)+" days"
        perfdata = "Uptime="+str(uptime)
        plugin_out(status, string, perfdata)
    else:
        string = "Server uptime is : "+str(days)+" days"
        perfdata = "Uptime="+str(uptime)
        plugin_out(status, string, perfdata)

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
        check_ping(host)
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
    elif command == "check_fans":
        check_fans()
    elif command == "check_psu":
        check_psu()
    elif command == "check_uptime":
        check_uptime()
    else:
        print "Seems like you selected an invalid option, please try ./check_cleversafe.py --help for options.."
        exit(2)


#main function
run_command(command)
