#!/proj/sot/ska3/flight/bin/python

import os
import argparse
import getpass
import traceback
from astropy.io import misc

#Alert Email Addresses
ACE_ADMIN = ['sot_ace_alert@cfa.harvard.edu']
HRC_ADMIN = ['sot_ace_alert@cfa.harvard.edu']

#TODO, following testing, replace alert email with red alert email
#HRC_ADMIN = ['sot_red_alert@cfa.harvard.edu']
