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

# GOES-16+ Energy bands (MeV) and combinations
DE = {'p1': [1.86, 1.020],
      'p2a': [2.300, 1.900],
      'p2b': [3.340, 2.310],
      'p3': [6.480, 3.400],
      'p4': [11.000, 5.840],
      'p5': [23.270, 11.640],
      'p6': [38.100, 25.900],
      'p7': [73.400, 40.300],
      'p8a': [98.500, 83.700],
      'p8b': [118.000, 99.900],
      'p8c': [143.000, 115.000],
      'p9': [242.000, 160.000],
      'p5p6': [23.270, 11.640],
      'p8abc': [143.000, 83.700],
      'p8abcp9': [242.000, 83.700]}
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
