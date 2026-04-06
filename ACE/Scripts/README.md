# Update ACE Realtime HTML Page

## Scripts:

- ace_wrap_script: Sets environment variable settings and calls ace_main_script.
- ace_main_script: Runs the following python scripts.

- update_ace_data_files.py: update ace related data files

        - input: none but read from:
                - ftp: 'https://services.swpc.noaa.gov/text/ace-epam.txt'
                - <ephem_dir>/Data/PE.EPH.gsme_spherical
                - <kp_dir>/Data/k_index_data_past
        - output: <ace_data_dir>/ace.archive
                - <ace_data_dir>/ace_12h_archive
                - <ace_data_dir>/ace_7day_archive
                - <ace_data_dir>/longterm/ace_data.txt
                - <ace_data_dir>/fluace.dat
                - <ace_data_dir>/kp.dat

- plot_p3_data.py: create scaled p3 data plot

        - input: none but read from <data_dir>/ace_7day_archive
        - output: <ace_plot_dir>/mta_ace_plot_P3.png

- create_ace_html_page.py: read ace data and update html page

        - input:  none, but read from:
                - http://services.swpc.noaa.gov/images/ace-epam-7-day.gif
                - http://services.swpc.noaa.gov/images/ace-mag-swepam-7-day.gif
                - <ace_dir>/Data/ace_12h_archive
        - output: <html_dir>/ACE/ace.html

- compute_fluence_cxo70.py: create a html page displaying ace fluence when cxo is above 70km

        - input:  none but read from:
                - <ephem_dir>/Data/PE.EPH.gsme_spherical
                - <ace_dir>/Data/ace_7day_archive
        - output: <html_dir>/ACE/ace_flux_dat.html

- alert_ace.py: Intake the last two hours worth of ACE data and calculate P3 fluence. If over the limit, send alert.
        Additionally parse the last 12 hours with of data to check validity. If invalid, send a warning email to notify a lack of up-to-date ACE rates.
        Sends a spectral index violation alert if the P5/P6 ratio is too high.

        - input: <ace_data_dir>/ace_12h_archive
        - output: alert emails

### Cron Variables:
###### Primary
```
SPACE_WEATHER=/data/mta4/Space_Weather
SPACE_WEATHER_WEB=/data/mta4/www/RADIATION
SPACE_WEATHER_URL=https://cxc.cfa.harvard.edu/mta/RADIATION
ENV_FLIGHT=/proj/sot/ska3/flight
```
###### Secondary
```
SPACE_WEATHER=/data/mta/Script/Space_Weather
SPACE_WEATHER_WEB=/data/mta/www/MIRROR/Space_Weather
SPACE_WEATHER_URL=https://ops-web.cfa.harvard.edu/mta/Space_Weather
ENV_FLIGHT=/proj/sot/ska3/flight
```
### Cron Job:

###### Primary (mta@boba-v):
```
3-59/5 * * * * ${ENV_FLIGHT}/bin/skare ${SPACE_WEATHER}/ACE/Scripts/ace.sh >> ${HOME}/Logs/ace_main_new.cron 2>&1
4-59/5 * * * * cd ${SPACE_WEATHER}/ACE/Scripts; ${ENV_FLIGHT}/bin/skare python alert_ace.py -m flight >> ${HOME}/Logs/ace_main_new.cron 2>&1
```
###### Secondary (mta@r2d2-v):
```
3-59/5 * * * * ${ENV_FLIGHT}/bin/skare ${SPACE_WEATHER}/ACE/Scripts/ace.sh >> ${HOME}/Logs/ace_main_mirror.cron 2>&1
4-59/5 * * * * cd ${SPACE_WEATHER}/ACE/Scripts; ${ENV_FLIGHT}/bin/skare python alert_ace.py -m flight >> ${HOME}/Logs/ace_main_mirror.cron 2>&1
```