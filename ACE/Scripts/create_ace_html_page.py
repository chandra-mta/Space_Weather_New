#!/usr/bin/env /data/mta4/Script/Python3.8/envs/ska3-shiny/bin/python

import os
import re
import argparse
import numpy as np
from Chandra.Time import DateTime
from astropy.table import Table, unique


# ftp, html sites with ACE data

HTTP_EPAM = "http://services.swpc.noaa.gov/images/ace-epam-7-day.gif"
HTTP_MAG = "http://services.swpc.noaa.gov/images/ace-mag-swepam-7-day.gif"

# Set ACE P3 scaling parameters

P3_P5_SCALE = 7.           # scale P5 to P3 values, while P3 is broke
P3_P6_SCALE = 36.          # scale P6 to P3 values, while P3 is broke
P3_P7_SCALE = 110.         # scale P7 to P3 values, while P3 is broke


def get_options():
    parser = argparse.ArgumentParser(description='ACE data and fluence')
    parser.add_argument('--ace_dir', type=str,
                        default='/data/mta4/Space_Weather/ACE/',
                        help='Root directory for ACE data and scripts')
    parser.add_argument('--html_dir', type=str,
                        default='.',
                        help='Root directory for ACE html output')
    args = parser.parse_args()
    return args


def create_ace_html_page():
    """
    Read 2h ACE data from local MTA 12h archive
    and update MTA's ACE html page at <html_dir>/ACE/ace.html.
    Download ACE images from:
    http://services.swpc.noaa.gov/images/ace-epam-7-day.gif
    http://services.swpc.noaa.gov/images/images/ace-mag-swepam-7-day.gif
    """

    args = get_options()

    # read 12h local MTA ACE archive data
    ifile = f"{args.ace_dir}/Data/ace_12h_archive"

    dat = read_2h_ace_data_from_12h_archive(ifile)

    ace_table = ''

    if len(dat) > 0:
        # There are nominal quality data in the last 2 hours,
        # so create a string, ace_table, with data for html display.
        # However, some channels may still contain bad data
        # indicated by -1.e5 values. These are going to be
        # displayed but filtered out before computing the stats.

        # Add scaled P5 and P6
        dat['p3_scaled_p5'] = dat['p5'] * P3_P5_SCALE
        dat['p3_scaled_p6'] = dat['p6'] * P3_P6_SCALE

        # ace_table with data for html display

        cols = ("yr", "mo", "da", "hhmm", "de1", "de4",
                "p2", "p3", "p3_scaled_p5", "p3_scaled_p6",
                "p5", "p6", "p7")
        row_format = ' '.join(["{:s} " * 4, "{:11.3f} " * 9, "\n"])

        for row in dat:
            ace_table = ace_table + row_format.format(*row[cols])

        # Add a header for the table with stats

        with open(f"{args.ace_dir}/Scripts/Template/header2") as fp:
            header = fp.read()

        ace_table = ace_table + "\n" + header

        # Calculate electron/proton stats (mean, min, 2h fluence, spectra)

        stats = calculate_stats(dat)

        # Add table with stats for the display

        for stat, name, fmt in zip((stats['means'], stats['mins'], stats['fluences_2h']),
                                    ('AVERAGE', 'MINIMUM', 'FLUENCE'),
                                    ('{:11.3f}', '{:11.3f}', '{:11.4e}')):
            vals = stat.values()
            row_format = ' '.join([f"{name.ljust(15)}", f"{fmt} " * len(vals), "\n"])
            ace_table = ace_table + row_format.format(*list(vals))

        # Add info on spectral indexes

        ace_table = ace_table + "\n" + "%7s %11s %11.3f %11s %11.3f %11s %11.3f %11s %11.3f \n\n"\
                       % ("SPECTRA        ", "p3/p5", stats['spectra']['p3_p5'],
                                             "p3/p6", stats['spectra']['p3_p6'],
                                             "p5/p6", stats['spectra']['p5_p6'],
                                             "p6/p7", stats['spectra']['p6_p7'])

        ace_table = ace_table + "%62s %4.1f\n"\
                       % ("*   This P3 channel is currently scaled from P5 data. P3* = P5 X ",
                          P3_P5_SCALE)

        ace_table = ace_table + "%62s %4.1f\n"\
                       % ("**  This P3 channel is currently scaled from P6 data. P3** = P6 X ",
                          P3_P6_SCALE)

        ace_table = ace_table + "%62s %4.1f\n"\
                       % ("*** This P3 channel (not shown) is currently scaled from P7 data. P3*** = P7 X ",
                          P3_P7_SCALE)

    else:
        # No valid data in the last 2h
        ace_table = """
<p style='padding-top:40px;padding-bottom:40px;'>
 No valid data for last 2 hours.
</p>
"""

    # download images and reverse the color:
    download_img(img=HTTP_EPAM,
                 html_dir=args.html_dir,
                 ace_dir=args.ace_dir)
    download_img(img=HTTP_MAG,
                 html_dir=args.html_dir,
                 ace_dir=args.ace_dir)

    # read in headers, footers and image html from template files
    # and insert ace_table string with current data and stats
    contents = []
    files = ['header', 'header1', 'image2', 'footer']
    for file in files:
        with open(f"{args.ace_dir}/Scripts/Template/{file}") as fp:
            contents.append(fp.read())

    contents.insert(2, ace_table)

    # update ACE html page
    with open(f"{args.html_dir}/ACE/ace.html", "w") as fo:
        fo.write("\n".join(contents))


def read_2h_ace_data_from_12h_archive(fname):
    """
    Reads 12h ACE archive and keeps only the last 2h
    of nominal quality (both the e_status and p_status
    flags equal 0).

    :param fname: ACE 12h local MTA archive
    :returns: astropy Table with ACE data
    """

    # TODO: update scripts that create the 12h archive to
    # include the column names
    names = ("yr", "mo", "da", "hhmm", "mjd", "mjdsec",
             "e_status", "de1", "de4",
             "p_status", "p2", "p3", "p5", "p6", "p7", "anis_index")

    formats = ('S4', 'S2', 'S2', 'S4', 'f8', 'f8',
               'i1', 'f8', 'f8',
               'i1', 'f8', 'f8', 'f8', 'f8', 'f8', 'i1')

    dat = np.loadtxt(fname, dtype={'names': names, 'formats' : formats})
    dat = Table(dat)

    # remove duplicate lines; TODO check why they appear
    dat = unique(dat, keys=("yr", "mo", "da", "hhmm"))

    # keep only the most recent two hours of nominal quality data
    fits_fmt = [f"{yr}-{mo.zfill(2)}-{da}T{hhmm[:2]}:{hhmm[-2:]}:00.000"
                for yr, mo, da, hhmm in zip(dat['yr'], dat['mo'],
                                            dat['da'], dat['hhmm'])]

    tt = DateTime(np.array(fits_fmt), format='fits').date
    now_minus_2h = DateTime(DateTime() - 2 / 24).date

    # status: 0 = nominal, 4,6,7,8 = bad data, unable to process, 9 = no data
    ok = (dat['e_status'] == 0) & (dat['p_status'] == 0) & (tt > now_minus_2h)
    dat = dat[ok]

    return dat


def calculate_stats(dat):
    """
    Calculate statistics: means, mins, 2h fluences in each channel,
    and spectral indexes.
    :param dat: astropy Table with ACE data
    :returns stats: dictionary with values being dictionaries of stats
                    for ACE channels
    """

    stats = {'means': {}, 'mins': {}, 'fluences_2h': {}, 'spectra': {}}

    cols = ("de1", "de4", "p2", "p3", "p3_scaled_p5", "p3_scaled_p5",
            "p5", "p6", "p7")

    for col in cols:
        # Filter out negative (bad) values
        ok = dat[col] > 0
        if len(dat[col][ok]) > 2:
            # At least 2 measurements of nominal quality
            # in the last 2 hours
            stats['means'][col] = np.mean(dat[col][ok])
            stats['mins'][col] = np.min(dat[col][ok])
            stats['fluences_2h'][col] = np.mean(dat[col][ok]) * 7200
        else:
            stats['means'][col] = -1e5
            stats['mins'][col] = -1e5
            stats['fluences_2h'][col] = -1e5

    # Spectral indexes
    stats['spectra'] = {'p3_p5': stats['means']['p3'] / stats['means']['p5'],
                        'p3_p6': stats['means']['p3'] / stats['means']['p6'],
                        'p5_p6': stats['means']['p5'] / stats['means']['p6'],
                        'p6_p7': stats['means']['p6'] / stats['means']['p7']}

    return stats


def download_img(img, html_dir, ace_dir, chg=1):
    """
    Download image from web site. Save image in {args.html_dir}/ACE/Plots

    :param img: web address of the image
    :param html_dir: root dir of space weather html products
    :param ace_dir: space weather ACE directory 
    :param chg: if > 0, reverse the color
    """

    # get the name of output img file name

    atemp = re.split('\/', img)
    ofile = atemp[-1]
    oimg = f"{html_dir}/ACE/Plots/{ofile}"

    # download the img

    try:
        cmd = f'wget -q -O {oimg} {img}'
        os.system(cmd)
    except:
        mc = re.search('gif', oimg)
        if mc is not None:
            cmd = f"cp {ace_dir}/Scripts/Template/no_plot.gif {oimg}"
        else:
            cmd = f"cp {ace_dir}/Scripts/Template/no_data.png {oimg}"
        os.system(cmd)

        return

    # reverse the color of the image

    if chg == 1:
        cmd = f'convert -negate {oimg} {oimg}'
        os.system(cmd)


#---------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    create_ace_html_page()

