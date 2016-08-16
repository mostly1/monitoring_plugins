#!/bin/bash

#Author: J. Mazzone
#Purpose: Plugin to monitor cleversafe slice stores and accessors. 
#Designed to gather most common hardware metrics.
#requires get_parsed_info.sh to be installed on controller.
###################################################################

#params
#HOST_IP=$1
CONTROLLER_IP="10.64.80.113"

usage(){
echo "Usage ./check_cleversafe -H <HOST IP> <FLAG>:"
echo "Flags:"
echo "-l = check_load"
echo "-t = check_temp"
echo "-c = check_dsnet_core"
echo "-d = check_dsnet_md"
echo "-s = check_ssh"
echo "-n = check_ntp"
echo "-m = check_memory"
echo "-r = check_cron"
echo "-p = check_ping"
echo ""

}


#check_load function
check_load(){
WARN=750
CRIT=1200
DATA_TYPE="statistic"

LOAD[0]=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "load\s+=" | awk -F "=" '{print $2}')
LOAD[1]=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "loadX.average1 " | awk -F "=" '{print $2}' | sed -e 's: ::g')
LOAD[5]=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "loadX.average5 " | awk -F "=" '{print $2}' | sed -e 's: ::g')
LOAD[15]=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "loadX.average15 " | awk -F "=" '{print $2}' | sed -e 's: ::g')
for i in {0,1,5,15}; do
	if [ ${LOAD[i]} -ge ${WARN} ]; then 
		if [ ${LOAD[i]} -ge ${CRIT} ]; then 
			echo "CRITICAL - Load values are reporting ${LOAD[i]}"
			exit 2
		else 
			echo "WARNING - Load values are reporting ${LOAD[i]}"
			exit 1
		fi
	fi
done
echo "OK - Load values are Currently: ${LOAD[0]} - 1M:  ${LOAD[1]} - 5M:  ${LOAD[5]}  - 15M: ${LOAD[15]}"
exit 0
}

#check memory
check_memory(){
WARN=10
CRIT=5
DATA_TYPE="statistic"

MEM_TOT_RAW=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "memory.MemTotal " | awk -F "=" '{print $2}' | sed -e 's: ::g')
MEM_AVAIL_RAW=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "memory.MemAvailable " | awk -F "=" '{print $2}' | sed -e 's: ::g')
MEM_TOT=$((${MEM_TOT_RAW} / 1024**3))
MEM_AVAIL=$((${MEM_AVAIL_RAW} / 1024**3))
if [ ${MEM_AVAIL} -le ${WARN} ]; then 
	if [ ${MEM_AVAIL} -le ${CRIT} ]; then 
		echo "CRITICAL - Only ${MEM_AVAIL}GB memory left available.."
		exit 2
	else 
		echo "WARNING - Only ${MEM_AVAIL}GB memory left available.."
		exit 1
	fi
fi
echo "OK - Total memory: ${MEM_TOT}GB - Memory Available: ${MEM_AVAIL}GB "
exit 0
}

#process states
#check_ssh function
check_ssh(){
DATA_TYPE="state"
SSH=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "process.ssh.status "| awk -F "=" '{print $2}' | sed -e 's: ::g')
if [ ${SSH} = "OK"  ]; then 
	echo "OK - SSH process is running."
	exit 0
else
	echo "CRITICAL - SSH process is reporting ${SSH}"
	exit 2
fi
}

#check_cron function
check_cron(){
DATA_TYPE="state"
CRON=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "process.cron.status "| awk -F "=" '{print $2}' | sed -e 's: ::g')
if [ ${CRON} = "OK" ];then
	echo "OK - CRON process is running."
	exit 0
else
	echo "CRITICAL - CRON process is reporting ${CRON}"
	exit 2
fi
}

#check_ntp function
check_ntp(){
DATA_TYPE="state"
NTP=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "process.ntp.status "| awk -F "=" '{print $2}' | sed -e 's: ::g')
if [ ${NTP} = "OK" ]; then 
	echo "OK - NTP process is running."
	exit 0
else
	echo "CRITICAL - NTP process is reporting ${NTP}"
fi
}

#check_dsnet_core funtion
check_dsnet_core(){
DATA_TYPE="state"
DSNET_CORE=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "process.dsnet-core.status "| awk -F "=" '{print $2}' | sed -e 's: ::g')
if [ ${DSNET_CORE} = "OK"  ];then
	echo "OK - DSNET_CORE process is running."
	exit 0
else 
	echo "CRITICAL - DSNET_CORE process is reporting ${DSNET_CORE}"
	exit 2
fi

}

#check dsnet_md function
check_dsnet_md(){
DATA_TYPE="state"
DSNET_MD=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep -E "process.dsnet-md.status "| awk -F "=" '{print $2}' | sed -e 's: ::g')
if [ ${DSNET_MD} = "OK" ]; then
	echo "OK - DSNET_MD process is running."
	exit 0
else
	echo "CRITICAL - DSNET_MD process is reporting ${DSNET_MD}"
	exit 2
fi

}

#check_temp function
check_temp(){

WARN=140
CRIT=150
DATA_TYPE="statistic"

CPU_TEMP=$(ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ./get_parsed_info.sh ${HOST_IP} ${DATA_TYPE} | grep  -E "cpuTemp" | grep -iE "0\.temperature" | awk -F "=" '{print $2}' | sed -e 's: ::g')
CPU_TEMP_F=$((${CPU_TEMP}*9/5+32))
if [ ${CPU_TEMP_F} -ge ${WARN} ]; then
	if [ $CPU_TEMP_F -ge ${CRIT} ]; then 
		echo "CRITICAL - CPU Temp is reporting ${CPU_TEMP_F}F"
		exit 2
	else 
		echo "WARNING - CPU is reporting ${CPU_TEMP_F}F"
		exit 1
	fi
fi  
echo "OK - CPU temp is reporting ${CPU_TEMP_F}F"
exit 0
}

#ping function for hostalive checks 
check_ping(){
ping_result=$(sudo ssh -Ai /home/nagios/nagios_key root@${CONTROLLER_IP} ping ${HOST_IP} -c 1| grep -iE "Unreachable")
if [ -z "${ping_result}" ]; then 
	exit 0
else
	exit 2
fi
}

#main case statement for script
while getopts ":H:ltcdsnmrp" FLAG; do 
	case ${FLAG} in
		H)
		HOST_IP="${OPTARG}"
		;;
		l)
		check_load
		;;
		t)
		check_temp
		;;
		c)
		check_dsnet_core
		;;
		d)
		check_dsnet_md
		;;
		s)
		check_ssh
		;;
		n)
		check_ntp
		;;
		m)
		check_memory
		;;
		r)
		check_cron
		;;
		p)
		check_ping
		;;
		*)
		echo "Please enter a valid option...."
		usage
		;;
	esac
done
