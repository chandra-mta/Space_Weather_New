# Extract KP Index 

Download kp index from:
- https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json
- https://www-app3.gfz-potsdam.de/kp_index/qlyymm.tab

and update various data files

## Script:

- fetch_kp_tables.py --- download and update the files
    - in addition to sorting the KP index in ECSV format, also stores legacy solar wind format for /data/mta/Script/Ephem

## Cron Job:

mta on boba-v
14 0,3,6,9,12,15,18,21 * * * /data/mta4/Space_Weather/KP/Scripts/kp_wrap_script  >> $HOME/Logs/kp_index_update.cron 2>&1

