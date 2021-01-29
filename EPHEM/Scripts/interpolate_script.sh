#!/bin/sh
if ps -ef | grep -v grep | grep "/data/mta4/Space_Weather/EPHEM/Scripts/ephem_interpolate.py"; then
    exit 0
else
    /data/mta4/Space_Weather/EPHEM/Scripts/ephem_interpolate.py
    exit 0
fi

