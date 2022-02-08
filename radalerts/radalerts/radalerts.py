#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

"""
ACE and GOES radiation alerting for Chandra.

Included alerts:
    - ACE P3 2-hour fluence exceeded 3.6e8, i.e. 50,000 x 2 x 3600
    - No nominal ACE data for >12h
    - GOES HRC shield proxy limit exceeded 195000, i.e. ~3 x 256 x 248
      (3 x SCS107 trip limit)

Adding new alerts:
    - edit alert.json file
    - add get_message_<alert> method to Alert class
    - add module method to define pars[<alert>] in main()

Disabling alerts:
    - touch <name>.logfile in working directory; this can be also used
      to extend the time an alert is disabled after being triggered so
      that the log file is not removed automatically after 24h
    - or edit alerts.json and change manual_disable from 0 to 1.

TODO:
    - option that would allow various alerts to be sent to different mailing lists
    - requires adding "email" in alerts.json and removing email from args
"""

import os
import sys
import time
import numpy as np
import argparse
from pprint import pformat
from Chandra.Time import DateTime
import tables

ALLOWED_MODES = ("test", "flight")

#PATH = '/proj/sot/ska3/flight/data/arc'
HOME = os.environ.get('HOME')
PATH = f"{HOME}/git/Space_Weather_New"

ACE_H5 = f"{PATH}/ACE.h5"
HRC_SHIELD_H5 = f"{PATH}/hrc_shield.h5"


def get_options():
    """
    """
    parser = argparse.ArgumentParser(description='Radiation Alerts')
    parser.add_argument('--email', type=str,
                        default='mtadude@cfa.harvard.edu',
                        help='Mailing list')
    parser.add_argument('--mode', type=str,
                        default='test',
                        help='Execution mode ("test", "flight")')
    args = parser.parse_args()
    return args


def get_current_hour():
    """
    Get current hour for the night time block
    of space weather alerts
    """
    t = time.ctime() # date and time
    t = t.split(' ')[-2] # time
    t = t.split(":")[0] # hour
    return int(t)


def remove_after_24h(fname):
    """
    Remove alert lock file after 24 hours
    """
    t_created = os.stat(fname) # sec
    t_now = time.time() # sec
    dt = t_now - t_created.st_mtime
    if dt > 24 * 3600:
        os.remove(fname)


class Alert(object):
    """
    Alert object
    """

    def __init__(self, mode, name, subject, email, val, url):
        """
        """
        self.mode = mode # 'flight', 'test'
        self.name = name
        self.email = email
        self.logfile = f"{name}.log"
        self.val = val
        self.url = url

        self.get_subject(subject)

        message_method = getattr(self, f'get_message_{name}')
        message_method()


    def get_subject(self, subject):
        """
        """
        if self.mode == 'test':
            self.subject = f'TEST {subject}'
        else:
            self.subject = subject


    def get_message_ace_12h_status(self):
        """
        """
        self.message = f"""No valid ACE data for at least 12h
Radiation team should investigate
This message sent to {self.email}
"""


    def get_message_acep3_2h_fluence(self):
        """
        """
        self.message = f"""A radiation violation of P3 (130keV) has been observed by ACE
Observed = {self.val}
(limit = fluence of 3.6e8 particles/cm2-ster-MeV within 2 hours)
see {self.url}
The ACIS on-call person should review the data and call a telecon if necessary.
This message sent to {self.email}
"""


    def get_message_hrc_shield(self):
        self.message = f"""A radiation violation of GOES HRC shield proxy has been observed
Observed = {self.val} Hz
(SCS107 trip limit = 195000 Hz)
see {self.url}
This message sent to {self.email}
"""


    def send_alert(self):
        """
        Send an alert email
        """
        with open(self.logfile, "w") as fh:
            fh.write(self.message)
        cmd = f'cat {self.logfile} | mailx -s "{self.subject}" {self.email}'
        if self.mode == 'test':
            print(cmd)
        elif self.mode == 'flight':
            os.system(cmd)


    def __repr__(self):
        return (' '.join([f'<{self.__class__.__name__}:',
                          f'name={self.name}',
                          f'mode={self.mode}',
                          f'val={self.val}',
                          f'email={self.email}>']))


    def __str__(self):
        return pformat(self.__dict__)


def get_ace_p3():
    """
    Read arc ACE.h5 file, check if there are nominal p3 data
    in the last 12h, compute 2h p3 fluence
    """

    # ACE
    try:
        with tables.open_file(ACE_H5, mode='r',
                              filters=tables.Filters(complevel=5, complib='zlib')) as h5:
            table = h5.root.data
            time = table.col('time')
            p3 = table.col('p3')

            # nominal ACE P3 entries in the last 12h
            ok = (time > DateTime().secs - 12 * 3600) & (p3 > 0)
            if len(p3[ok]) > 0:
                status = True
            else:
                status = False

            # compute p3 2h fluence
            ok = (time > DateTime().secs - 2 * 3600) & (p3 > 0)
            if len(p3[ok]) > 0:
                fluence = np.median(p3[ok]) * 2 * 3600
            else:
                fluence = None

            h5.root.data.flush()

    except (OSError, IOError, tables.NoSuchNodeError):
        print("Warning: No previous ACE data, exiting")
        sys.exit(0)

    return status, fluence


def get_hrc_shield():
    """
    Read arc hrc_shield.h5 file, get most recent
    goes hrc_shield proxy
    """

    # HRC shield proxy
    try:
        with tables.open_file(HRC_SHIELD_H5, mode='r',
                              filters=tables.Filters(complevel=5, complib='zlib')) as h5:
            table = h5.root.data
            hrc_shield = table.col('hrc_shield')[-1]
            lasttime = table.col('time')[-1]
            h5.root.data.flush()

            # GOES data comes every 5 min
            #if lasttime < DateTime().secs - 20 * 60:
            if lasttime < DateTime().secs - 6 * 60 * 60: # 6h for testing with local file
                print(DateTime(lasttime).date)
                print("Warning: No recent GOES data, data older than 20 min")
                sys.exit(0)

    except (OSError, IOError, tables.NoSuchNodeError):
        print("Warning: No previous GOES data, exiting")
        sys.exit(0)

    return hrc_shield


def trigger_alerts(a, pars):
    """
    Check alerts against limits and trigger alerts
    with violations; record the value that violated
    the limit
    """

    name = a['name']

    # process bool alerts
    if a['type'] == "bool":
        if not pars[name]:
            a['triggered'] = True
            a['val'] = 0

    # process upper limits
    if a['type'] == "upper":
        val = pars[name]
        if val > a['limit']:
            a['triggered'] = True
            a['val'] = val

    # process lower limits
    if a['type'] == 'lower':
        val = pars[name]
        if val < a['limit']:
            a['triggered'] = True
            a['val'] = val

    return a


def send_alert(a, mode, email):
    """
    """
    alert = Alert(mode=mode,
                  name=a['name'],
                  subject=a['subject'],
                  email=email,
                  val=a['val'],
                  url=a['url'])

    if a['manual_disable']:
        return

    if os.path.exists(alert.logfile):
        remove_after_24h(alert.logfile)
    else:
        alert.send_alert()


def main():
    """
    Check ACE and HRC violations
    1. No ACE data for > 12h -> sot_ace_alert
    2. ACE P3 2hr fluence > 3.6e8 -> sot_ace_alert
    3. HRC proxy > 3 x SCS107 trip limit given the uncertainty
       in evaluating the proxy -> sot_ace_alert
    """

    args = get_options()

    if args.mode not in ALLOWED_MODES:
        raise ValueError("Execution mode should be 'test' (default) or 'flight'")

    pars = {}
    pars['ace_12h_status'], pars['acep3_2h_fluence'] = get_ace_p3()
    pars['hrc_shield'] = get_hrc_shield()

    with open("alerts.json", "r") as fh:
        alerts = json.load(fh)

    alerts = Table(alerts['alerts'])
    alerts['triggered'].dtype = bool

    t = get_current_hour()

    for a in alerts:

        a = trigger_alerts(a, pars)

        if a['triggered'] & (t > a['blackout_tstop']) & (t < a['blackout_tstart']):
            send_alert(a, mode=args.mode, email=args.email)

#----------------------------------------------------------------------------------

if __name__ == "__main__":

    main()
