# Solar Wind Density and Speed Prediction

This directory contains files to predict and plot the solar wind
environment for Chandra, 4 weeks into the future.

## Scripts

- solar_wind_wrap_script: Environment setting scripts
- solar_wind_main_script: Environment setting scripts
- create_predicted_solar_wind_plot.py : The script to obtain data, predict future trends and plot the data.

### Input
- SWEPAM_LINK = 'https://services.swpc.noaa.gov/json/ace/swepam/ace_swepam_1h.json'
- MTOF_LINK = f"https://l1.umd.edu/data/<NOW.datetime.year>_CELIAS_Proton_Monitor_5min.zip"
- <ephem_dir>/Data/PE.EPH.gsme_spherical

### Output
- <soho_data_dir>/<NOW.datetime.year>_CELIAS_Proton_Monitor_5min.txt
- <soho_plot_dir>/solwin.png
- <orbit_plot_dir>/solwin.png

## Web address:
https://cxc.cfa.harvard.edu/mta/RADIATION/Orbit/orbit.html

## cron job

mta on boba-v
36 0,3,6,9,12,15,18,21 * * *  cd /data/mta4/Space_Weather/SOHO/Scripts; /data/mta4/Space_Weather/SOHO/Scripts/solar_wind_wrap_script >> $HOME/Logs/soho_solwin_new.cron 2>&1