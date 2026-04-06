#!/usr/bin/env python
"""
**pull_swpc_media.py**: Fetches SWPC media for use in the GOES X-Ray webpage

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Apr 09, 2025

:INFO:
    - https://sdo.gsfc.nasa.gov/data/rules.php
    - https://sdo.gsfc.nasa.gov/assets/docs/HMI_M.ColorTable.pdf

# /// testing
# tested-ska-release = "2026.1"
# ///
"""
import os
import argparse
import json
import math
from urllib.parse import urlparse
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from astropy.table import Table
from pathlib import Path
import io
import requests
import urllib.request
#
#--- Define Directory Pathing
#
SPACE_WEATHER_WEB = Path(os.environ.get('SPACE_WEATHER_WEB', "/data/mta4/www/RADIATION"))
GOES_MEDIA_DIR : Path = SPACE_WEATHER_WEB / "GOES" / "Media"
#
# --- Links to media sources
#
CCOR_1_7DAYS = 'https://services.swpc.noaa.gov/products/ccor1/mp4s/ccor1_last_7_days.mp4'
MAGNETOGRAM_MAP = 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_2048_HMIBC.jpg'
SOLAR_REGIONS = 'https://services.swpc.noaa.gov/json/solar_regions.json'

TODAY = datetime.now().strftime("%Y-%m-%d")

def download_img(url):
    """
    Download image
    """
    #: Create response object
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content))
    return img

def download_video(url, file_out):
    """
    Download video, and save directly to a file.
    """
    #: Create response object
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        with open(file_out, 'wb') as f:
            for chunk in resp.iter_content(chunk_size = 1024*1024): 
                if chunk: 
                    f.write(chunk)

def _filename(url):
    return os.path.basename(urlparse(url).path)

def swpc_media():
    """
    Periodically pull SWPC media for GOES web pages.
    """
    #: CCOR_1 Video
    video_file = GOES_MEDIA_DIR / _filename(CCOR_1_7DAYS)
    download_video(CCOR_1_7DAYS, video_file)

    #: Solar Regions
    with urllib.request.urlopen(SOLAR_REGIONS, timeout = 10) as url:
        raw_json = json.loads(url.read().decode())
    all_regions_table = Table(rows = raw_json)
    todays_regions = all_regions_table[all_regions_table['observed_date'] == TODAY]

    #: Magnetogram Map
    img = download_img(MAGNETOGRAM_MAP)
    annotated_img = img.copy()
    w,h = annotated_img.size
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
    draw = ImageDraw.Draw(annotated_img)

    #: Annotate the magnetogram image with the active region locations
    for region in todays_regions:
        lat = region['latitude']
        long = -region['longitude']
        x,y = _to_pixel(w,h,lat,long)
        draw.text((x-112,y+48),str(region['region']), fill='white', font=font)
    
    _annotated_image_file = GOES_MEDIA_DIR / "annotated_sdo_hmi_magnetogram.png"
    annotated_img.save(_annotated_image_file)
    annotated_img.close()
    img.close()

def _deg2rad(deg):
    return (deg * math.pi) /180

def _to_pixel(w,h,lat,long):
    """
    Use image size to convert lat, long coordinates into pixel locations
    
    :w,h: The pixel size of the image
    :lat: Latitude
    :long: Longitude
    """
    spacing = int(w * 0.042) #: Pixel distance inward of edge of picture to edge of map
    #: Origin of pixel coordinate system is top left
    map_width = w - 2 * spacing
    
    #: Spherical coordinates
    radius = map_width / (2) #: Pixel Units
    latRad = _deg2rad(lat)
    longRad = _deg2rad(long)
    #: Conversion to Cartesian (Origin in center of map is tangent point of image plane to sphere surface)
    
    #: Note that latitude is polar angle with different starting point and axis direction, therefore convert linearly
    horizontal = radius * math.sin((math.pi/2) - latRad) * math.sin(longRad)
    vertical = radius * math.cos((math.pi/2) - latRad)
    
    #: Convert from Cartesian coordinate origin to image origin and rightward downward axis directions.
    x = int(horizontal + w/2)
    y = int(h/2 - vertical)
    
    return x,y

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", help = "Determine data output file path")
    args = parser.parse_args()

    if args.mode == 'test':
        if args.path:
            GOES_MEDIA_DIR = Path(args.path)
        else:
            GOES_MEDIA_DIR = Path(os.getcwd(), "test", "_outTest", "GOES", "Media")
        os.makedirs(GOES_MEDIA_DIR, exist_ok=True)

    swpc_media()