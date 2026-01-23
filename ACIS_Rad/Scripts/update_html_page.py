#!/proj/sot/ska3/flight/bin/python
"""
**update_html_page.py**: update radiation related html page

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Jan 23, 2026

# /// testing
# tested-ska-release = "2026"
# ///
"""
import os
import argparse
import calendar
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
#
# --- Define Directory Pathing
#
WEB_DIR = "/data/mta4/www/RADIATION/ACIS_Rad"

UTC_NOW = datetime.now(timezone.utc)
UTC_LAST_MONTH = UTC_NOW + relativedelta(months=-1)
YEARS = [str(i) for i in range(UTC_LAST_MONTH.year, 1999, -1)]
MONTHS = [i for i in calendar.month_abbr[1:]]


#
# --- Template Globals
#
_JINJA_ENV = Environment(loader = FileSystemLoader('Template', followlinks = True))

def get_options(args=None):
    parser = argparse.ArgumentParser(description="Update ACIS Radiation Correlation Pages")
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    opt = parser.parse_args(args)
    return opt

def render_index():
    """
    Generate the Main ACIS Radiation Correlation Page.
    """
    subhtmls = {}
    for year in YEARS:
        subhtmls[year] = {}
        for i, month in enumerate(MONTHS):
            #: Fill with a link to the subpage if we are path the target month.
            #: Subtracted by one for different month enumeration.
            if (int(year) < UTC_LAST_MONTH.year) or (i <= UTC_LAST_MONTH.month - 1):
                subhtmls[year][month] = f'<a href="./Html/{month.lower()}{year[2:]}.html">{month.upper()}{year[2:]}</a>'    
    index_template = _JINJA_ENV.get_template('index.jinja')
    index_render = index_template.render(subhtmls=subhtmls,
                                         years=YEARS,
                                         months=MONTHS)
    with open(f"{WEB_DIR}/index.html", 'w') as f:
        f.write(index_render)

def render_month(year : str, month : str):
    """
    Generate the Monthly ACIS Radiation Correlation Pages

    :param year: Year of the ACIS Radiation Correlation
    :type year: str
    :param month: Month of the ACIS Radiation Correlation
    :type month: str

    """
    month_template = _JINJA_ENV.get_template('month.jinja')
    month_render = month_template.render(year = year,
                                         month = month)
    with open(f"{WEB_DIR}/Html/{month.lower()}{year[2:]}.html", 'w') as f:
        f.write(month_render)

if __name__ == "__main__":

    opt = get_options()

    if opt.mode == 'test':
        WEB_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(WEB_DIR, exist_ok = True)
        os.makedirs(f"{WEB_DIR}/Html", exist_ok = True)
        os.makedirs(f"{WEB_DIR}/Plot", exist_ok = True)
    
    render_index()
    render_month(
        year = str(UTC_LAST_MONTH.year),
        month = MONTHS[UTC_LAST_MONTH.month - 1]
    )