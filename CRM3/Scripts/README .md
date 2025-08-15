# The Chandra Radiation Model (CRM)
**Robert Cameron (October 2002)**
**Takashi Isobe (March 2020)**
**William Aaron (Aug 2025)**

## Description
The Chandra Radiation Model (CRM) from Sverdrup/MSFC
is propagated in this directory, and graphical and
tabular data products are updated every 5 minutes 
by cron jobs, to track current and future orbital 
proton flux and fluence.

## Table Script Set
**crm_table_wrap_script -> crm_table_main_script**
- create_crm_flux_table.py
- create_crm_summary.py
- plot_crm_flux_data.py

### create_crm_flux_table.py
Fetch all relevant data and calculate the CRM flux table for current orbit.
This replaces previous incarnations of the crm.pl script.
#### Input:
- /data/mta4/Space_Weather/CRM3/Data/CRM3_p.dat<kp>
- /data/mta4/Space_Weather/ACE/Data/ace_7day_archive
- /data/mta4/Space_Weather/KP/Data/kp_iaga.ecsv
- /proj/sot/acis/FLU-MON/FPHIST-2001.dat
- /proj/sot/acis/FLU-MON/GRATHIST-2001.dat

#### Output:
- /data/mta4/Space_Weather/CRM3/Data/crm_flux_table.ecsv (astropy csv file of different fluxes according to time and chandra config)
- /data/mta4/www/RADIATION/CRM/crm_flux_table.ecsv

### create_crm_summary.py
Summarize the CRM flux table into different data files to support legacy applications.
This replaces previous incarnations of the crm.pl script.
#### Input:
- /data/mta4/Space_Weather/CRM3/Data/crm_flux_table.ecsv
- /data/mta4/Space_Weather/EPHEM/Data/gephem.dat
- /data/mta4/Space_Weather/GOES/Data/goes_differential_protons.ecsv
- /data/mta4/Space_Weather/GOES/Data/goes_integral_electrons.ecsv

#### Output:
- /data/mta4/Space_Weather/CRM3/Data/CRMsummary.json (Summarization file of flux, fluence, orbit, and GOES at current time)
- /data/mta4/Space_Weather/CRM3/Data/CRMsummary.dat
- /data/mta4/www/RADIATION/CRM/CRMsummary.json
- /data/mta4/www/RADIATION/CRM/CRMsummary.dat

### plot_crm_flux_data.py
Create crm predicted flux plots

#### Input:
- /data/mta4/Space_Weather/CRM/Data/CRMsummary.dat
- /data/mta4/Space_Weather/EPHEM/Data/PE.EPH.gsme_spherical_short
- /data/mta4/Space_Weather/Comm_data/Data/dsn_summary.dat
- /data/mta4/Space_Weather/CRM/Data/CRM3_p.dat30
- /proj/sot/acis/FLU-MON/FPHIST-2001.dat
- /proj/sot/acis/FLU-MON/GRATHIST-2001.dat
#### Output:
- /data/mta4/www/RADIATION/Orbit/Plots/crmpl.png
- /data/mta4/www/RADIATION/Orbit/Plots/crmplatt.png

### runcrm 
Generate CRM fluxes at 5-minute intervals (corresponding 
to the Chandra ephemeris positions in 
/data/mta4/Space_Weather/ephem/PE.EPH.dat), 
for the 28 possible Kp values from 0.0 to 9.0

this script is run as a part of /data/mta4/Space_Weather/ephem/Scripts/ephem.pl

input  -- /data/mta4/Space_Weather/ephem/Data/PE.EPH.gsme_in_Re

output -- /data/mta4/Space_Weather/CRM3/Data/CRM_p.datNN

gfortran -std=legacy -ffixed-form -fd-lines-as-comments -ffixed-line-length-none  \
            runcrm.f /data/mta4/Space_Weather/CRMFLX/CRMFLX_V33o/CRMFLX_V33.f -o runcrm

#### Binary data compatibility
CRMFLX_V33.f needs three binary data files which are machine dependent.
if you need to recompile runcrm.f on none linux machine, you need to do the following.

1. go to linux machine (this version is complied on linux)

2. compile SolWB2A.f and run it. this will create an ascii version
    (SolWB2A.f can be found in /data/mta4/Space_Weather/CRMFLX/CRMFLX_V33/Data/)

3. go to a new machine/operation system.

4. compile SolWA2B.f and run it. this will create a binary version 
    which can be read on the new machine.

5. do same for two others. If you can't find a fortran program, specifically
    to that data, just modify  SolWB2A.f and/or  SolWA2B.f

The binary data files are:
- MSheath_Kp_PROT.BIN
- MSPH_Kp_PROT.BIN
- SolWind_Kp_PROT.BIN

The ascii versions are already in:
/data/mta4/Space_Weather/CRMFLX/CRMFLX_V33/Data/

## Cron Jobs
- **mta@boba-v**
- 21 3,6,9,12,18,21 * * *                    /data/mta4/Space_Weather/CRM3/Scripts/crm_wrap_script       >> $HOME/Logs/crm3_runcrm_new.cron       2>&1
- 4,9,14,19,24,29,34,39,44,49,54,59 * * * *  /data/mta4/Space_Weather/CRM3/Scripts/crm_table_wrap_script >> $HOME/Logs/crm3_create_table_new.cron 2>&1
- **mta@r2d2-v**
- 21 3,6,9,12,18,21 * * * /data/mta/Script/Space_Weather/CRM3/Scripts/crm_wrap_script
- 2,7,12,17,22,27,32,37,42,47,52,57 * * * * /data/mta/Script/Space_Weather/CRM3/Scripts/crm_table_wrap_script