#!/proj/sot/ska3/flight/bin/python
"""
**fetch_swfo_data.py.py**: Fetch the SWFO related data files

:Author: w. aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Sep 03, 2025

"""
import os
import json
import urllib
from astropy.table import Table
import numpy as np
from time import sleep
from cxotime import CxoTime
import argparse
import getpass
import signal