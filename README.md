# monitoring_plugins
Monitoring plugins for icinga2

**Plugins in this folder:** 

- **check_cleversafe.py** = Python plugin that uses cleversafe's internal API to check cluster health and stastical data. use "--help" for info about functionality 

- **check_cleversafe.sh** = Original plugin. Needs to have "get_parsed_info.sh" installed on controler to work. (only use if monitoring server cannot talk directly to other storage nodes). Uses ssh keys to connect securely. Make sure you have a key called nagios_key on all servers. 

- **get_parsed_info.sh** = Needed for check_cleversafe.sh to function. Must be installed on controller node. 

- **check_storagepools.py** = Requires creds.json with your own credentials to function. Gets individual storage pool totals from cleversafe API. host IP should be the controler. 

- **cluster_total.py** = Checks entire cleversafe storage cluster via API. use controler as host IP

- **check_switches.sh** = This plugin is old, probably the oldest one I wrote. It checks Arista switches and Dell Force10 switches for specific MIBS set in the script. This is a "works for me" type thing but I posted it incase anyone can use it. 
