#!/bin/bash

source /usr/lib/nagios/osdc_plugins/ipmi.cfg

#dcmi power reading info
power_reading(){
avg_watts=$(sudo ipmitool -I lanplus -U ADMIN -P ${ipmipw} -H ${host} dcmi power reading | grep "Average" | awk -F ":" '{print $2}' | awk -F " " '{print $1}')
instant_watts=$(sudo ipmitool -I lanplus -U ADMIN -P ${ipmipw} -H ${host} dcmi power reading | grep "Instantaneous" | awk -F ":" '{print $2}' | awk -F " " '{print $1}')
min_watts=$(sudo ipmitool -I lanplus -U ADMIN -P ${ipmipw} -H ${host} dcmi power reading | grep "Minimum" | awk -F ":" '{print $2}' | awk -F " " '{print $1}')
max_watts=$(sudo ipmitool -I lanplus -U ADMIN -P ${ipmipw} -H ${host} dcmi power reading | grep "Maximum" | awk -F ":" '{print $2}' | awk -F " " '{print $1}')
echo "OK - Average power usage in watts: ${avg_watts} | avg_watts=${avg_watts} Instantaneous=${instant_watts} Minimum=${min_watts} Maximum=${max_watts}"
exit 0
}

#check to see if host is up and ipmi configured before calling power function

alive(){
alive=$(sudo ipmitool -I lanplus -U ADMIN -P ${ipmipw} -H ${host} chassis power status | awk '{print $4}')
    if [ "${alive}" != "on"  ]; then
       echo "CRITICAL - host is off or IPMI not conifgured."
       exit 2
    fi
}

while getopts ":H:" opt; do
    case ${opt} in
        H )
            host=${OPTARG}
            alive
            power_reading ${host}
        ;;
        * )
            echo "please enter -H <host> to use this plugin"
        ;;
    esac
done
