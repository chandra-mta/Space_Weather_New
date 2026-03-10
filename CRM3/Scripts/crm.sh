#!/usr/bin/env bash
cd ${SPACE_WEATHER}/CRM3/Scripts

python create_crm_flux_table.py -m flight
python create_crm_summary.py -m flight
python plot_crm_flux_data.py -m flight

#: TODO incorporate the image editing into the plot generation python script for portability
convert /data/mta4/www/RADIATION/Orbit/Plots/crmpl.png -trim /data/mta4/www/RADIATION/Orbit/Plots/crmpl.png
convert /data/mta4/www/RADIATION/Orbit/Plots/crmplatt.png -trim /data/mta4/www/RADIATION/Orbit/Plots/crmplatt.png



