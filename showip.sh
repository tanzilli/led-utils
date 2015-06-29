#!/bin/sh
ip=`ifconfig wlan0 2>/dev/null|awk '/inet addr:/ {print $2}'|sed 's/addr://'`
./text.py $ip 0 0 1 1 
