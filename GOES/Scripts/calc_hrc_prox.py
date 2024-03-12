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

#
#--- Determine HRC Proxy Linear Combination parameters
#

#In use for transition period between GOES-15 and GOES-16+ (2020)
HRC_PROXY_V1 = {'CHANNELS': {'P5': 6000,
                             'P6': 6000,
                             'P7': 270000,
                             'P8A': 100000,
                             'P8B': 100000,
                             'P8C': 100000},
                'CONSTANT': 0}

#In use for new generation GOES-16+ (post 2020)
HRC_PROXY_V2 = {'CHANNELS': {'P5': 143,
                             'P6': 64738,
                             'P7': 162505}, 
                'CONSTANT': 4127}

# GOES-16+ Energy bands (keV) and combinations
DE = {'p1': [1860., 1020.],
      'p2a': [2300., 1900.],
      'p2b': [3340., 2310.],
      'p3': [6480., 3400.],
      'p4': [11000., 5840],
      'p5': [23270., 11640.],
      'p6': [38100., 25900.],
      'p7': [73400., 40300.],
      'p8a': [98500., 83700.],
      'p8b': [118000., 99900.],
      'p8c': [143000., 115000.],
      'p9': [242000., 160000.],
      'p5p6': [23270., 11640.],
      'p8abc': [143000., 83700.],
      'p8abcp9': [242000., 83700.]}

# Add delta_e to each list
for key in DE.keys():
    de = DE[key]
    de.append(de[0] - de[1])

#Based on HRC Proxy value at specific time
HRC_THRESHOLD = {'Warning': 6.2e4,
                 'Violation': 1.95e5}


def combine_rates_h5(dat, chans):
    """
    Return combined rates for multiple channels
    """
    combined = 0
    for chan in chans:
        combined = combined + dat[chan] * DE[chan][2]
        
    delta_e = DE[chans[-1]][0] - DE[chans[0]][1]
    return combined / delta_e
