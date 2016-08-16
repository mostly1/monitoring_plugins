#!/bin/bash


#################################################################################################
#Author:Jeff Mazzone                                                                            #
#Date:Oct 2014                                                                                  #
#Purpose:Nagios plugin to monitor specific MIBS from switches accross an internal network.      #
#Tested on Arista and Force 10 switches                                                         #
#################################################################################################
#IFS SETTINGS
IFS=""
#Debug settings
DEBUG_SW="FALSE"

#Set return states for nagios
STATE_OK="0"
STATE_WARNING="1"
STATE_CRITICAL="2"
STATE_UNKNOWN="3"
STATE_DEPENDENT="4"

#Set snmp path
SNMPWALK="/usr/bin/snmpwalk"

#Arguments
HOSTIP=$1
IF_PORT=$2
MONITOR_TYPE=$3
WARN=$4
CRIT=$5

#MIB settings

IN_ERRORS_ISO="iso.3.6.1.2.1.2.2.1.14."
OUT_ERRORS_ISO="iso.3.6.1.2.1.2.2.1.20."
SYSDESC="1.3.6.1.2.1.1.1"
ADMIN_STATUS_ISO="1.3.6.1.2.1.2.2.1.7."
OPER_STATUS_ISO="1.3.6.1.2.1.2.2.1.8."

#Display usage for plugin
function usage(){
	echo "Usage: check_switches.sh ipaddress interface_port monitor_type warn critical"
	echo "Monitor types are  \"in\" , \"out\" , \"isaup\" , \"isoup\""
}

#Set states for nagios
function set_state(){

ERROR_COUNT=$1
RAW=$2
	if [ -z "$*" ]; then
			usage
	else

		if [ "${ERROR_COUNT}" -eq "0" ]; then
			if [ ${DEBUG_SW} = "TRUE" ]; then
                	        echo "OK - "${RAW}
				echo "STATE: " ${STATE_OK}
                	fi
			echo "OK - "${RAW}
			exit ${STATE_OK}
		elif [ "${ERROR_COUNT}" -le "${WARN}" ]; then
        	        if [ ${DEBUG_SW} = "TRUE" ]; then
				echo "WARNING - "${RAW}
                        	echo "STATE: " ${STATE_WARNING}
                	fi
			echo "WARNING - "${RAW}
			exit ${STATE_WARNING}
		elif [ "${ERROR_COUNT}" -ge "${CRIT}" ]; then
			if [ ${DEBUG_SW} = "TRUE" ]; then
                        	echo "CRITICAL - "${RAW}
				echo "STATE: " ${STATE_CRITICAL}
                	fi
			echo "CRITICAL - "${RAW}
			exit ${STATE_CRITICAL}
		else
                	if [ ${DEBUG_SW} = "TRUE" ]; then
				echo "UNKNOWN - "${RAW}
                        	echo "STATE: " ${STATE_UNKNOWN}
                	fi
			echo "UNKNOWN - "${RAW}
			exit ${STATE_UNKNOWN}
		fi

	fi

}

#get ifInErrors from switch
function in_errors(){
	IN_ERROR_RAW=$(${SNMPWALK} -v 2c -c public ${HOSTIP} ${IN_ERRORS_ISO}${IF_PORT})
	IN_ERROR_COUNT=$(echo ${IN_ERROR_RAW} | awk '{print $NF}' )
	if [ ${DEBUG_SW} = "TRUE" ]; then
		echo "DEBUG: snmpwalk -v 2c -c public ${HOSTIP} ${IN_ERRORS_ISO}${IF_PORT} | awk '{print $NF}'"
		echo "ERROR_COUNT: " ${IN_ERROR_COUNT}
		echo "ERROR_RAW: " ${IN_ERROR_RAW}
	fi
	set_state ${IN_ERROR_COUNT} ${IN_ERROR_RAW}
}
#get ifOutErrors from Switch
function out_errors(){
        OUT_ERROR_RAW=$(${SNMPWALK} -v 2c -c public ${HOSTIP} ${OUT_ERRORS_ISO}${IF_PORT})
        OUT_ERROR_COUNT=$(echo ${OUT_ERROR_RAW} | awk '{print $NF}')
	if [ ${DEBUG_SW} = "TRUE" ]; then
                echo "DEBUG: snmpwalk -v 2c -c public ${HOSTIP} ${IN_ERRORS_ISO}${IF_PORT} | awk '{print $NF}'"
                echo "ERROR_COUNT: " ${OUT_ERROR_COUNT}
		echo "ERROR_RAW: " ${OUT_ERROR_RAW}
        fi
	set_state ${OUT_ERROR_COUNT} ${OUT_ERROR_RAW}
}
#Determine up down for interfaces and send to state selector
function up_down(){
if [ ${DEBUG_SW} = "TRUE" ]; then
	echo "UP_DOWN PARAMS: " $1 $2
fi
UP="0"
DOWN="9999"
UNKNOWN="unknown"

case ${1} in
	"up(1)")
		set_state ${UP} ${2}
	;;
	"down(2)")
		set_state ${DOWN} ${2}
	;;
	*)
		set_state ${UNKNOWN} ${2}
	;;
esac

}
#get admin status
function admin_status(){
	A_STATUS_RAW=$(${SNMPWALK} -v 2c -c public ${HOSTIP} ${ADMIN_STATUS_ISO}${IF_PORT})
	A_STATUS=$(echo ${A_STATUS_RAW} | awk '{print $NF}')
	if [ ${DEBUG_SW} = "TRUE" ]; then
		echo "ADMIN_STATUS PARAMS: " ${A_STATUS} ${A_STATUS_RAW}
		echo "snmpwalk -v 2c -c public ${HOSTIP} ${ADMIN_STATUS_ISO}${IF_PORT}"
	fi
	up_down ${A_STATUS} ${A_STATUS_RAW}

}
#get oper status
function oper_status(){
        O_STATUS_RAW=$(${SNMPWALK} -v 2c -c public ${HOSTIP} ${OPER_STATUS_ISO}${IF_PORT})
        O_STATUS=$(echo ${O_STATUS_RAW} | awk '{print $NF}')
	if [ ${DEBUG_SW} = "TRUE" ]; then
		echo "OPER_STATUS PARAMS: " ${O_STATUS} ${O_STATUS_RAW}
		echo "snmpwalk -v 2c -c public ${HOSTIP} ${OPER_STATUS_ISO}${IF_PORT}"
	fi
	up_down ${O_STATUS} ${O_STATUS_RAW}

}

if [ ${DEBUG_SW} = "TRUE" ]; then
	echo "****DEBUGGING IS ENABLED! DONT PANIC!****"
	echo "PARAMS: "$HOSTIP $IF_PORT $MONITOR_TYPE $WARN $CRIT
fi
#check what type of monitor we want to use and send params.
case ${MONITOR_TYPE} in
		in)
		  in_errors ${HOSTIP} ${IF_PORT} ${WARN} ${CRIT}
		;;
		out)
		  out_errors ${HOSTIP} ${IF_PORT} ${WARN} ${CRIT}
		;;
		isaup)
		  admin_status ${HOSTIP} ${IF_PORT}
		;;
		isoup)
		  oper_status ${HOSTIP} ${IF_PORT}
		;;
		*)
                  echo "Your syntax for this plugin is incorrect. Please correct your arguments and try again"
        	  usage
		;;
esac
