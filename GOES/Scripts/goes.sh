#!/usr/bin/env bash
cd ${SPACE_WEATHER}/GOES/Scripts

python fetch_goes_tables.py -m flight
python plot_goes_data.py -m flight
python update_goes_html_page.py -m flight