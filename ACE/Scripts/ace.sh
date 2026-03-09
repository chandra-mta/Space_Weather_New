#!/usr/bin/env bash
cd ${SPACE_WEATHER}/ACE/Scripts

python update_ace_data_files.py -m flight
python plot_p3_data.py -m flight
python create_ace_html_page.py -m flight
python compute_fluence_cxo70.py -m flight
python alert_ace.py -m flight
