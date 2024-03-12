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
DE = {'P1': [1860., 1020.],
      'P2A': [2300., 1900.],
      'P2B': [3340., 2310.],
      'P3': [6480., 3400.],
      'P4': [11000., 5840.],
      'P5': [23270., 11640.],
      'P6': [38100., 25900.],
      'P7': [73400., 40300.],
      'P8A': [98500., 83700.],
      'P8B': [118000., 99900.],
      'P8C': [143000., 115000.],
      'P9': [242000., 160000.],
      'P5P6': [23270., 11640.],
      'P8ABC': [143000., 83700.],
      'P8ABCP9': [242000., 83700.]}

# Add delta_e to each list
for key in DE.keys():
    de = DE[key]
    de.append(de[0] - de[1])

#Based on HRC Proxy value at specific time
HRC_THRESHOLD = {'Warning': 6.2e4,
                 'Violation': 1.95e5}

#For fixing the format in importing goes_data_r.txt
COLNAMES = ['Time',
            'P1',
            'P2A',
            'P2B',
            'P3',
            'P4',
            'P5',
            'P6',
            'P7',
            'P8A',
            'P8B',
            'P8C',
            'P9',
            'P10',
            'HRC_Proxy']

def combine_rates_h5(dat, chans):
    """
    Return combined rates for multiple channels
    """
    combined = 0
    for chan in chans:
        combined = combined + dat[chan] * DE[chan][2]
        
    delta_e = DE[chans[-1]][0] - DE[chans[0]][1]
    return combined / delta_e
