#!/usr/bin/env bash
cd ${SPACE_WEATHER}/CRM3/Scripts

python create_crm_flux_table.py -m flight
python create_crm_summary.py -m flight
python plot_crm_flux_data.py -m flight