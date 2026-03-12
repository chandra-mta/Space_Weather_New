# Extract KP Index 

Download kp index from:
- https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json
- https://www-app3.gfz-potsdam.de/kp_index/qlyymm.tab

and update various data files

## Script:

- fetch_kp_tables.py --- download and update the files
    - in addition to sorting the KP index in ECSV format, also stores legacy solar wind format for /data/mta/Script/Ephem

### Cron Variables:
- Primary
    - SPACE_WEATHER=/data/mta4/Space_Weather
    - ENV_FLIGHT=/proj/sot/ska3/flight
- Secondary
    - SPACE_WEATHER=/data/mta/Script/Space_Weather
    - ENV_FLIGHT=/proj/sot/ska3/flight

### Cron Job:

- Primary (mta@boba-v):
14 */3 * * * cd ${SPACE_WEATHER}/KP/Scripts; ${ENV_FLIGHT}/bin/skare python fetch_kp_tables.py -m flight >> ${HOME}/Logs/kp_index_update.cron 2>&1

- Secondary (mta@r2d2-v):
14 */3 * * * cd ${SPACE_WEATHER}/KP/Scripts; ${ENV_FLIGHT}/bin/skare python fetch_kp_tables.py -m flight >> ${HOME}/Logs/kp_index_update_mirror.cron 2>&1