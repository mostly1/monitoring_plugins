#!/usr/bin/python

import os

status = os.access('/var/lib/nova/instances',os.W_OK)
if str(status) == "False":
    print 'CRITICAL - /var/lib/nova/instances is not writable..'
    exit(2)
elif str(status) == "True":
    print 'OK - /var/lib/nova/instances is writable..'
    exit (0)
else:
    print 'UNKNOWN - Cannot read output or something went wrong..'
    exit(3)
