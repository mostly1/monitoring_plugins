#!/bin/bash

HOST_IP=$1
DATA_TYPE=$2

sudo ssh -Ai /home/nagios/nagios_key localadmin@${HOST_IP} health ${DATA_TYPE}
