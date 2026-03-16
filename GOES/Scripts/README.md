# GOES proton/particle monitoring system for Chandra.

Note: Goes proton channel name and the energy band:

P1          1020-1860 keV
P2A         1900-2300 keV
P2B         2310-3340 keV
P3          3400-6480 keV
P4          5840-11000 keV
P5          11640-23270 keV
P6          25900-38100 keV
P7          40300-73400 keV
P8A         83700-98500 keV
P8B         99900-118000 keV
P8C         115000-143000 keV
P9          160000-242000 keV
P10         276000-404000 keV

## Scripts:

- collect_goes_long.py: update a long term goes data

        - input:  
                - https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json
        - output:
                - <goes_data_dir>/goes_data_r.txt (note there is goes_data.txt which is from older goes satellites and have 2001 - early Mar 2020)

- swpc_media.py: Daily pull of SWPC and SDO media for the GOES X-ray page
        
        - input:
                - https://services.swpc.noaa.gov/products/ccor1/mp4s/ccor1_last_7_days.mp4
                - https://sdo.gsfc.nasa.gov/assets/img/latest/latest_2048_hmibc.jpg
                - https://services.swpc.noaa.gov/json/solar_regions.json
        - output: 
                - <goes_media_dir>/ccor1_last_7_days.mp4
                - <goes_media_dir>/latest_2048_HMIBC.jpg
                - <goes_media_dir>/annotated_sdo_hmi_magnetogram.png
                - <goes_media_dir>/Media/solar_regions.json

- check_archive.py: checks validity of hrc proxy archive in case goes.sh fails

        - input: 
                - <goes_data_dir>/hrc_proxy.csv
        - output:
                - email to mtadude in case of a time discrepancy in archive.

- goes.sh: Bash shell script for running all the 5-minutely GOES data products (data files, plots, and web pages)

- fetch_goes_tables.py: Fetch GOES particle tables and data from SWPC NOAA

        - input:
                - https://services.swpc.noaa.gov/json/goes/primary/differential-protons-3-day.json
                - https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json
                - https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-3-day.json
                - https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json
                - https://services.swpc.noaa.gov/json/edited_events.json
        - output:
                - <goes_data_dir>/goes_differential_protons.ecsv
                - <goes_data_dir>/goes_integral_protons.ecsv
                - <goes_data_dir>/goes_integral_electrons.ecsv

- plot_goes_data.py: Get and plot goes data.

        - input:
                - <goes_data_dir>/goes_differential_protons.ecsv
                - <goes_data_dir>/goes_integral_protons.ecsv
        - output:
                - <goes_plot_dir>/goes_protons.png
                - <goes_plot_dir>/goes_particles.png

- update_goes_html_page.py: update goes differential, integral, and x-ray pages

        - input:
                - https://services.swpc.noaa.gov/json/goes/primary/differential-protons-1-day.json
                - https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json
                - https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json
        - output:
                - <goes_data_dir>/Gp_pchan_5m.txt
                - <goes_data_dir>/Gp_part_5m.txt
                - <goes_data_dir>/goes_flares.ecsv
                - <goes_web_dir>/goes_pchan_p.html
                - <goes_web_dir>/goes_part_p.html
                - <goes_web_dir>/goes_xray_p.html

- alert_hrc.py: send hrc proxy alerts

        - input:
                - <goes_data_dir>/Gp_pchan_5m.txt
        - output:
                - email alerts
                - <goes_data_dir>/hrc_proxy.csv
                - <goes_data_dir>/hrc_proxy_viol.json

## Cron Variables:
###### Primary
```
SPACE_WEATHER=/data/mta4/Space_Weather
ENV_FLIGHT=/proj/sot/ska3/flight
SPACE_WEATHER_WEB=/data/mta4/www/RADIATION
SPACE_WEATHER_URL=https://cxc.cfa.harvard.edu/mta/RADIATION
```
###### Secondary
```
SPACE_WEATHER=/data/mta/Script/Space_Weather
ENV_FLIGHT=/proj/sot/ska3/flight
SPACE_WEATHER_WEB=/data/mta/www/MIRROR/Space_Weather
SPACE_WEATHER_URL=https://ops-web.cfa.harvard.edu/mta/Space_Weather
```

## Cron Job

The swpc_media.py script marks active solar regions marked as observed or still observed on the current date
Therefore, we do not run the script too early in the day in case the days' active regions have not been updated yet.

###### Primary (mta@boba-v):
```
14 2 * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python collect_goes_long.py -m flight >> ${HOME}/Logs/goes_long_term_new.cron 2>&1
30 2 * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python swpc_media.py -m flight >> ${HOME}/Logs/swpc_media.cron 2>&1

2-59/5 * * * * ${ENV_FLIGHT}/bin/skare ${SPACE_WEATHER}/goes.sh >> ${HOME}/Logs/goes_main_new.cron 2>&1
3-59/5 * * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python alert_hrc.py -m flight >> ${HOME}/Logs/goes_main_new.cron 2>&1
4-59/5 * * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python check_archive.py -m flight >> ${HOME}/Logs/goes_archive_check.cron 2>&1
```

###### Secondary (mta@r2d2-v):
```
14 2 * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python collect_goes_long.py -m flight >> ${HOME}/Logs/goes_long_term_mirror.cron 2>&1
30 2 * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python swpc_media.py -m flight >> ${HOME}/Logs/swpc_media_mirror.cron 2>&1

2-59/5 * * * * ${ENV_FLIGHT}/bin/skare ${SPACE_WEATHER}/goes.sh >> ${HOME}/Logs/goes_main_mirror.cron 2>&1
3-59/5 * * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python alert_hrc.py -m flight >> ${HOME}/Logs/goes_main_mirror.cron 2>&1
4-59/5 * * * * cd ${SPACE_WEATHER}/GOES/Scripts; ${ENV_FLIGHT}/bin/skare python check_archive.py -m flight >> ${HOME}/Logs/goes_archive_check_mirror.cron 2>&1
```