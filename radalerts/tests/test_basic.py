"""
pytest -s tests/test_basic.py --email <test_mailing_list>
pytest -s tests/test_basic.py::<method> --email <test_mailing_list>

The tests defaults to mtadude@cfa.harvard.edu
without --email option(see conftest.py)
"""

import numpy as np
import os
import time
from radalerts import *
from astropy.table import Table

TESTMODE = 'test'

# Alerts with violations
ALERTS = [{'name': 'ace_12h_status',
           'triggered': False,
           'subject': 'ACE no valid data for >12h',
           'type': 'bool',
           'manual_disable': 0,
           'limit': 0,
           'val': 0,
           'logfile': 'ace_12h_status.log',
           'url': 'https://test.com/ace.html'},

          {'name': 'acep3_2h_fluence',
           'triggered': False,
           'subject': 'ace p3',
           'type': 'upper',
           'manual_disable': 0,
           'limit': 3.6e8,
           'val': 1e9,
           'logfile': 'acep3_2h_fluence.log',
           'url': 'https://test.com/ace.html'},

          {'name': 'hrc_shield',
           'triggered': False,
           'subject': 'hrc shield',
           'type': 'upper',
           'manual_disable': 0,
           'limit': 195000,
           'val': 1e6,
           'logfile': 'hrc_shield.log',
           'url': 'https://test.com/ace.html'}]


def test_alert_object(email):

    alert = Alert(mode=TESTMODE,
                  name='ace_12h_status',
                  subject='test',
                  email=email,
                  val=None,
                  url='https://test.com/ace')

    assert alert.subject == f"TEST test"
    assert alert.message == f"""No valid ACE data for at least 12h
Radiation team should investigate
This message sent to {alert.email}
"""

    alert = Alert(mode=TESTMODE,
                  name='acep3_2h_fluence',
                  subject='test',
                  email=email,
                  val=0,
                  url='https://test.com/goes')

    assert alert.subject == f"TEST test"
    assert alert.message == f"""A radiation violation of P3 (130keV) has been observed by ACE
Observed = {alert.val}
(limit = fluence of 3.6e8 particles/cm2-ster-MeV within 2 hours)
see {alert.url}
The ACIS on-call person should review the data and call a telecon if necessary.
This message sent to {alert.email}
"""

    alert = Alert(mode=TESTMODE,
                  name='hrc_shield',
                  subject='test',
                  email=email,
                  val=0,
                  url='https://test.com')

    assert alert.subject == f"TEST test"
    assert alert.message == f"""A radiation violation of GOES HRC shield proxy has been observed
Observed = {alert.val} Hz
(SCS107 trip limit = 195000 Hz)
see {alert.url}
This message sent to {alert.email}
"""

def test_trigger_alerts():
    """
    """
    pars = {'ace_12h_status': False,
            'acep3_2h_fluence': 1e9,
            'hrc_shield': 1e6}

    alerts = Table(ALERTS)
    alerts['val'] = np.array([None, 0, 0])

    for a in alerts:
        a = trigger_alerts(a, pars)

    assert np.all([a['triggered'] for a in alerts])


def test_send_alert_1(email):
    """
    Test that new alerts are sent (new = no logfiles)
    Expected result: three emails received and logfiles
    created.
    """

    alerts = Table(ALERTS)

    for a in alerts:
        if os.path.exists(a['logfile']):
            os.remove(a['logfile'])

    for a in alerts:
        send_alert(a, mode=TESTMODE, email=email)

    assert np.all([os.path.exists(a['logfile']) for a in alerts])


def test_send_alert_2(email):
    """
    Test that alerts are blocked if logfiles exist. If emails with
    subject "TEST failed" are recieved then the test failed.
    """

    alerts = Table(ALERTS)

    for a in alerts:
        a['subject'] = 'lockfile disable failed'
        send_alert(a, mode=TESTMODE, email=email)

    # Test that logfiles are old, older than 0.005 sec
    dts = []
    for a in alerts:
        dt = time.time() - os.path.getctime(a['logfile']) # sec
        dts.append(dt)

    assert np.all([dt > 0.005 for dt in dts])


def test_send_alert_3(email):
    """
    The send_alert routine is called twice in this test:
    1st time to test that logfiles are removed after 24h,
    2nd time to test that alerts are sent after removing old
    logfiles. Expected result: three emails received with
    subject 'after 24h' and new logfiles.
    """

    alerts = Table(ALERTS)

    for a in alerts:
        # set timestamp of logfiles to 24h and 2 mins in the past
        t = time.time() - 24 * 3600 - 120
        stamp = time.strftime('%Y%m%d%H%M', time.localtime(t))
        os.system(f"touch -t {stamp} {a['logfile']}")
        a['subject'] = 'after 24h'
        send_alert(a, mode=TESTMODE, email=email) # removes logfiles
    
    # Test that logfiles are removed
    assert np.all([not os.path.exists(a['logfile']) for a in alerts])
    
    for a in alerts:
        send_alert(a, mode=TESTMODE, email=email) # sends a new alert

    # Test that logfiles are new, younger than 1 sec
    dts = []
    for a in alerts:
        dt = time.time() - os.path.getctime(a['logfile']) # sec
        dts.append(dt)

    assert np.all([dt < 1 for dt in dts])

    # Clean up
    for a in alerts:
        os.remove(a['logfile'])
            

def test_send_alert_4(email):
    """
    Test 'manual_disable' option. Alter logfiles to be >24h old but set
    'manual_disable' to 1 (True). Test that alerts remain blocked.
    """

    alerts = Table(ALERTS)
    
    # Manually disable all alerts
    alerts['manual_disable'] = np.array([1, 1, 1])

    for a in alerts:
        t = time.time() - 30 * 3600 # 30h old logfile
        stamp = time.strftime('%Y%m%d%H%M', time.localtime(t))
        os.system(f"touch -t {stamp} {a['logfile']}")
        a['subject'] = 'manual disable failed'
        send_alert(a, mode=TESTMODE, email=email) # removes logfiles

    # Test that logfiles are older than 24h
    dts = []
    for a in alerts:
        dt = time.time() - os.stat(a['logfile']).st_mtime # sec
        dts.append(dt)

    assert np.all([dt > 24 * 3600 for dt in dts])

    # Clean up
    for a in alerts:
        os.remove(a['logfile'])
