#!/proj/sot/ska3/flight/bin/python
"""
**create_crm_flux_table.py**: Fetch all relevant data and calculate the CRM flux table for current orbit

:Author: w. aaron (William.aaron@cfa.harvard.edu)
:Last Updated: Aug 08, 2025

# /// testing
# tested-ska-release = "2026.1"
# ///
"""

import os
import bisect
from astropy.io import ascii
from astropy.table import Table, unique, vstack
from kadi import events
from cxotime import CxoTime
from datetime import datetime, timedelta
import numpy as np
from django.db import close_old_connections, utils
import argparse
import getpass
import signal

#
# --- Define Directory Pathing
#
CRM_WEB_DIR = "/data/mta4/www/RADIATION/CRM3"
CRM_DATA_DIR = "/data/mta4/Space_Weather/CRM3/Data"
OUT_CRM_WEB_DIR = "/data/mta4/www/RADIATION/CRM3"
OUT_CRM_DATA_DIR = "/data/mta4/Space_Weather/CRM3/Data"
ACE_DATA_DIR = "/data/mta4/Space_Weather/ACE/Data"
KP_DATA_DIR = "/data/mta4/Space_Weather/KP/Data"
FP_FILE = "/proj/sot/acis/FLU-MON/FPHIST-2001.dat"
GRAT_FILE = "/proj/sot/acis/FLU-MON/GRATHIST-2001.dat"
#
# --- Globals
#
SW_FACTOR = [0, 1, 2, 0.5]  #: Indexed according to the CRM solar region index marker.
CRM_FACTOR = [0, 0, 1, 1]  #: Indexed according to the CRM solar region index marker.
CXONOW = CxoTime()
TDELTA = 300
SOL_REGION = [
    "NULL",
    "Solar_Wind",
    "Magnetosheath",
    "Magnetosphere",
]  #: Indexed according to the CRM solar region index marker.
#
# --- Column Globals
#
_INPUT_ACE_COLUMNS = [
    "year",
    "month",
    "day",
    "hhmm",
    "mjd",
    "daysecs",
    "electron_status",
    "electron38-53",
    "electron175-315",
    "proton_status",
    "proton47-68",
    "proton115-195",
    "proton310-580",
    "proton795-1193",
    "proton1060-1900",
    "aniso",
]  #: For reading in ACE data file.
_P3_CHANNEL = "proton115-195"  #: Channel selection for ACE P3 alert.

COLUMN_DESCRIPTIONS = {
    "cxosecs": "Seconds since 1998-01-01T00:00:00 (TT)",
    "kp": "KP Index",
    "sol_region_idx": "Index of Solar Region of Chandra. ['NULL', 'Solar_Wind', 'Magnetosheath', 'Magnetosphere']",
    "crm_proton_flux": "CRM (runcrm fortran) mean estimate of proton flux",
    "instrument": "Latest instrument at time point in FP",
    "grating": "Latest grating at time point in FP",
    "ace_p3_flux": "Flux of the ACE p3 Channel 115-195 KeV",
    "corrected_crm_flux": "Linear combination of crm_proton_flux and ace_p3_flux according to solar region",
    "attenuated_crm_flux": "Corrected CRM flux with scaling factor dependent on instrument and grating configuration.",
}  #: Column descriptions for crm_flux_table.ecsv

COLUMN_UNITS = {
    "cxosecs": "s",
    "crm_proton_flux": "protons/(cm^2*s*sr*MeV)",
    "ace_p3_flux": "protons/(cm^2*s*sr*MeV)",
    "corrected_crm_flux": "protons/(cm^2*s*sr*MeV)",
    "attenuated_crm_flux": "protons/(cm^2*s*sr*MeV)",
}  #: Column units for crm_flux_table.ecsv

#: Additional columns provided in CRM3_p.datXX (where XX is KP from 00 to 90, corresponding to values 0.0 and 9.0)
#: are as follows from the documentation of the CRMFLX_V33.f code.
#: These differ from the mean provided crm_proton_flux for each 5-minute average.
#: FLUX95 is the 95% level uniform solar wind flux as modeled by the CRM.
#: FLUX50 is the 50% level uniform solar wind flux as modeled by the CRM.
#: FLUXSD is the standard deviation of solar wind flux as modeled by the CRM.
_CRM_DATA_COL_NAMES = (
    "cxosecs",
    "sol_region_idx",
    "crm_proton_flux",
    "FLUX95",
    "FLUX50",
    "FLUXSD",
)


def create_crm_flux_table():
    """
    Create the CRM flux table
    """
    orbit_data = fetch_orbit()
    current_table = None
    current_metadata = {}
    if os.path.isfile(f"{OUT_CRM_DATA_DIR}/crm_flux_table.ecsv"):
        current_table = ascii.read(f"{OUT_CRM_DATA_DIR}/crm_flux_table.ecsv")
        start_fetch = CxoTime(current_table["cxosecs"][-1])
    else:
        #: If something happened to the current orbit's flux table, restart from scratch.
        start_fetch = orbit_data["orbit_start"]

    kp_table = read_kp(start_fetch)
    ace_table = read_ace(start_fetch)

    crm_flux_table = format_crm_flux_table(start_fetch, kp_table)
    crm_flux_table = add_instrument_config_file(crm_flux_table, start_fetch)
    crm_flux_table = add_ace_flux_column(crm_flux_table, ace_table)
    crm_flux_table = add_flux_attenuation(crm_flux_table)

    if current_table is not None:
        current_metadata = current_table.meta
        crm_flux_table = vstack([current_table, crm_flux_table], join_type="exact")
        crm_flux_table = unique(crm_flux_table, keys="cxosecs")

        #: If orbit has changed, check and create new table if necessary.
        if current_metadata.get("orbit_num") != orbit_data["orbit_num"]:
            previous_table = crm_flux_table[
                crm_flux_table["cxosecs"] <= orbit_data["orbit_stop"].secs
            ]
            new_table = crm_flux_table[
                crm_flux_table["cxosecs"] > orbit_data["orbit_start"].secs
            ]
            #: Even if there is a new orbit, we might not have flux for the latest orbit yet.
            #: Only record once we have flux.
            if len(new_table) > 0:
                previous_table.meta = current_metadata
                archive(previous_table)
                crm_flux_table = new_table
                crm_flux_table.meta.update(_coerce_date(orbit_data))
    else:
        #: No previous table, record orbit of brand new table
        crm_flux_table.meta.update(_coerce_date(orbit_data))
        for k, v in COLUMN_DESCRIPTIONS.items():
            crm_flux_table[k].description = v
        for k, v in COLUMN_UNITS.items():
            crm_flux_table[k].unit = v

    crm_flux_table.write(
        f"{OUT_CRM_DATA_DIR}/crm_flux_table.ecsv", overwrite=True, delimiter=","
    )


def archive(previous_table):
    """
    Write previous orbit's information to the CRM archive.
    """
    corrected_crm_fluence = sum(previous_table["corrected_crm_flux"] * TDELTA)
    attenuated_crm_fluence = sum(previous_table["attenuated_crm_flux"] * TDELTA)

    archive_table = ascii.read(f"{CRM_DATA_DIR}/CRMarchive.ecsv")
    archive_table.add_row(
        [
            previous_table.meta["orbit_start"],
            previous_table.meta["orbit_stop"],
            previous_table.meta["orbit_num"],
            corrected_crm_fluence,
            attenuated_crm_fluence,
        ]
    )
    archive_table.write(
        f"{OUT_CRM_DATA_DIR}/CRMarchive.ecsv", overwrite=True, delimiter=","
    )
    previous_table.write(
        f"{OUT_CRM_DATA_DIR}/previous_crm_flux_table.ecsv",
        overwrite=True,
        delimiter=",",
    )


def reconnect(func):
    """
    Function decorator which runs the django.db close connections method if we encounter a disk I/O error when using kadi.events
    """
    _freq = 2
    _errors = utils.OperationalError

    def wrapper_func(*args, **kwargs):
        _last_exception = None
        for i in range(_freq):
            try:
                return func(*args, **kwargs)
            except _errors as e:
                _last_exception = e
                close_old_connections()
        _last_exception.add_note(
            f"@reconnect ran function {_freq} times. Still encountered error."
        )
        raise _last_exception

    return wrapper_func


@reconnect
def fetch_orbit():
    """
    Read current orbit information from kadi
    """
    orbit_table = events.orbits.filter(start=CXONOW).table

    orbit_data = {
        "orbit_start": CxoTime(orbit_table["start"][0]),
        "orbit_stop": CxoTime(orbit_table["stop"][0]),
        "orbit_num": orbit_table["orbit_num"][0],
        "orbit_update_time": CXONOW,
    }
    return orbit_data


@reconnect
def fetch_moves(start_fetch):
    """
    Read TSC and Grating information from kadi
    """
    tsc_moves = events.tsc_moves.filter(start=start_fetch - timedelta(days=4)).table
    grating_moves = events.grating_moves.filter(
        start=start_fetch - timedelta(days=4)
    ).table
    return tsc_moves, grating_moves


def read_instrument_files(start_fetch):
    """
    Read the ACIS focal plane and grating history files to find planned instrument configuration up to now.

    :WARNING: This file contains the planned instrument configuration, therefore it is not perfectly consistent to
    actual times of when instrument or grating is in place as confirmed by command history, nor does it factor in radiation interruptions.
    """
    fp_table = ascii.read(
        FP_FILE, data_start=19000, names=("cxotime", "instrument", "obsid")
    )  #: History spans to 2001, start later then select.
    sel_fp = fp_table["cxotime"] >= start_fetch - timedelta(days=4)
    fp_table = fp_table[sel_fp]

    grat_table = ascii.read(
        GRAT_FILE, data_start=7050, names=("cxotime", "hetg", "letg", "obsid")
    )  #: History spans to 2001, start later then select.
    sel_grat = grat_table["cxotime"] >= start_fetch - timedelta(days=4)
    grat_table = grat_table[sel_grat]
    return fp_table, grat_table


def read_kp(start_fetch):
    """
    Read the most recent observed / estimated value for the KP index.
    """
    kp_table = ascii.read(f"{KP_DATA_DIR}/kp_iaga.ecsv")
    #: Note that the kp_forecast_table is fetched every 3 hours,
    #: therefore the KP estimates can periodically be outdated.
    start_sel = kp_table["time_tag"] >= _z(start_fetch - timedelta(hours=3))
    stop_sel = kp_table["time_tag"] <= _z(CXONOW)
    sel = np.logical_and(start_sel, stop_sel)
    kp_table = kp_table[sel]
    return kp_table


def read_ace(start_fetch):
    """
    Read in the ACE flux for the desired time interval
    """
    ace_table = unique(
        ascii.read(f"{ACE_DATA_DIR}/ace_7day_archive", names=_INPUT_ACE_COLUMNS)
    )
    cxotime_col = _convert_time_format(
        ace_table["year"],
        ace_table["month"],
        ace_table["day"],
        ace_table["hhmm"],
    )
    ace_table.add_column(cxotime_col, name="cxosecs")
    start_sel = ace_table["cxosecs"] >= start_fetch
    stop_sel = ace_table["cxosecs"] <= CXONOW
    ace_table = ace_table[np.logical_and(start_sel, stop_sel)]

    corrected_p3 = np.zeros(len(ace_table))  #: Correct / ignore missing and low values.
    _valid = None
    _count = 0
    while _valid is None:
        if ace_table[_P3_CHANNEL][_count] >= 0:
            _valid = ace_table[_P3_CHANNEL][_count]
            if _valid < 1e-6:
                _valid = 0
        else:
            _count += 1
    for i, val in enumerate(ace_table[_P3_CHANNEL]):
        if val < 0:  #: Missing value.
            corrected_p3[i] = _valid
        elif 0 <= val < 1e-6:  #: Valid but nominally zero.
            corrected_p3[i] = 0
            _valid = 0
        else:
            corrected_p3[i] = val
            _valid = val
    ace_table[_P3_CHANNEL] = corrected_p3
    return ace_table


def intake_crm_table(kp):
    file = f"{CRM_DATA_DIR}/CRM3_p.dat{_kpi(kp)}"
    crm_data_table = ascii.read(file, names=_CRM_DATA_COL_NAMES)
    return crm_data_table


def format_crm_flux_table(start_fetch, kp_table):
    kp_to_crm_data = {kp: intake_crm_table(kp) for kp in set(kp_table["kp"])}

    #: Gather the crm data files in kp interval sections.
    cxosecs = []
    kp = []
    sol_region_idx = []
    crm_proton_flux = []

    start_interval_marker = start_fetch
    for row in kp_table:
        #: Runs first partial kp interval, then over all interior kp intervals.
        #: Every kp interval is 3 hours. Therefore the stop is 3 hours past the current row.
        #: Use the minimum so that once we reach the last row,
        #: our interval cuts off to the current time for the last partial kp interval.
        stop_interval_marker = min(
            CxoTime(row["time_tag"]) + timedelta(hours=3), CXONOW
        )
        _table = kp_to_crm_data[row["kp"]]
        sel = np.logical_and(
            _table["cxosecs"] >= start_interval_marker.secs,
            _table["cxosecs"] <= stop_interval_marker.secs,
        )
        _table = _table[sel]
        include_cxosecs = _table["cxosecs"].tolist()
        include_region = _table["sol_region_idx"].tolist()
        include_flux = _table["crm_proton_flux"].tolist()
        include_kp = [row["kp"] for _ in include_region]

        cxosecs += include_cxosecs
        sol_region_idx += include_region
        crm_proton_flux += include_flux
        kp += include_kp

        #: Setup the start_interval_marker for the next run.
        start_interval_marker = CxoTime(row["time_tag"]) + timedelta(hours=3)

    crm_flux_table = Table(
        [cxosecs, kp, sol_region_idx, crm_proton_flux],
        names=("cxosecs", "kp", "sol_region_idx", "crm_proton_flux"),
    )
    stop_sel = crm_flux_table["cxosecs"] <= CXONOW.secs
    crm_flux_table = crm_flux_table[stop_sel]
    return crm_flux_table


def add_instrument_config_file(crm_flux_table, start_fetch):
    """
    Use the ACIS instrument configuration files to determine the attenuation for the crm flux.
    """
    fp_table, grat_table = read_instrument_files(start_fetch)

    instrument = []
    grating = []
    for entry in crm_flux_table:
        entry_date = CxoTime(entry["cxosecs"]).date
        #: Bisect finds the index to insert a value into an array,
        #: therefore stepping back by one is the most recent state.
        inst_idx = bisect.bisect_left(fp_table["cxotime"], entry_date) - 1
        si = fp_table[inst_idx]["instrument"]
        instrument.append(si)

        grat_idx = bisect.bisect_left(grat_table["cxotime"], entry_date) - 1
        hetg = grat_table[grat_idx]["hetg"]
        letg = grat_table[grat_idx]["letg"]
        if hetg == "HETG-OUT" and letg == "LETG-OUT":
            otg = "NONE"
        elif hetg == "HETG-IN" and letg == "LETG-OUT":
            otg = "HETG"
        elif hetg == "HETG-OUT" and letg == "LETG-IN":
            otg = "LETG"
        elif hetg == "HETG-IN" and letg == "LETG-IN":
            otg = "BAD"
        grating.append(otg)
    crm_flux_table.add_column(instrument, name="instrument")
    crm_flux_table.add_column(grating, name="grating")

    return crm_flux_table


def add_instrument_config_kadi(crm_flux_table, start_fetch):
    """
    Use kadi events to fetch TSC and grating moves to determine instrument and grating for attenuating the flux

    :WARNING: This source provides instrument configuration based on known commands in the kadi archive. As such, this function only adds
    instrument configuration based on data since the last comm, and does not list the most up to date instrument configurations.
    """
    tsc_moves, grating_moves = fetch_moves(start_fetch)

    instrument = []
    grating = []
    for entry in crm_flux_table:
        #: Iterate through the TSC and grating moves to find corresponding instrument and grating.
        #: Bisect finds the index to insert a value into an array,
        #: therefore stepping back by one is the most recent state.
        tsc_idx = bisect.bisect_left(tsc_moves["tstop"], entry["cxosecs"]) - 1
        si = tsc_moves[tsc_idx]["stop_det"]
        instrument.append(si.strip())

        grat_idx = bisect.bisect_left(grating_moves["tstop"], entry["cxosecs"]) - 1
        if grating_moves[grat_idx]["direction"] == "RETR":
            otg = "NONE"
        else:
            otg = grating_moves[grat_idx]["grating"]
        grating.append(otg)
    crm_flux_table.add_column(instrument, name="instrument")
    crm_flux_table.add_column(grating, name="grating")

    return crm_flux_table


def add_ace_flux_column(crm_flux_table, ace_table):
    """
    Merge the two astropy tables, cutting to the time where both data sets contain values.
    ACE data tends to lag behind 5-10 minutes.
    """
    crm_flux_table = crm_flux_table[: len(ace_table)]
    ace_table = ace_table[: len(crm_flux_table)]

    crm_flux_table.add_column(ace_table[_P3_CHANNEL], name="ace_p3_flux")
    return crm_flux_table


def add_flux_attenuation(crm_flux_table):
    """
    Use solar region, instrument, and grating to calculate two additional flux columns.
    """
    crm_factors = [CRM_FACTOR[i] for i in crm_flux_table["sol_region_idx"]]
    sw_factors = [SW_FACTOR[i] for i in crm_flux_table["sol_region_idx"]]
    att_factors = _att_factor(
        crm_flux_table["instrument"].data, crm_flux_table["grating"].data
    )

    corrected = (
        crm_factors * crm_flux_table["crm_proton_flux"].data
        + sw_factors * crm_flux_table["ace_p3_flux"].data
    )
    attenuated = att_factors * corrected
    crm_flux_table.add_column(corrected, name="corrected_crm_flux")
    crm_flux_table.add_column(attenuated, name="attenuated_crm_flux")
    return crm_flux_table


def _z(arg):
    """
    Corrective internal function to yield ISOZ formatted datetimes
    """
    if isinstance(arg, CxoTime):
        return arg.isot.split(".")[0] + "Z"
    elif isinstance(arg, datetime):
        return arg.isoformat().split(".")[0] + "Z"


def _kpi(kp):
    """
    Corrective KP index float to CRM filename format
    """
    return f"{kp:.1f}".replace(".", "")


def _coerce_date(arg):
    """
    Corrective internal function to coerce CxoTime into date
    """
    if isinstance(arg, CxoTime):
        return arg.date
    elif isinstance(arg, dict):
        return {k: _coerce_date(arg[k]) for k in arg.keys()}
    elif isinstance(arg, list):
        return [_coerce_date(i) for i in arg]
    else:
        return arg


@np.vectorize
def _convert_time_format(year, month, day, hhmm):
    """Converts separated ``numpy.ndarray`` containing date information into an array of ``CxoTime`` objects.

    :param year: Four digit year
    :type year: int
    :param month: Month
    :type month: int
    :param day: Day
    :type day: int
    :param hhmm: Integer Combining Hours and Minutes
    :type hhmm: int
    :return: ``numpy.ndarray`` of ``CxoTime`` objects.
    :rtype: ``numpy.ndarray(dtype = 'object')``

    """
    hh = hhmm // 100  #: Hours in hundreds and thousands place.
    mm = hhmm % 100  #: Minutes in tens and ones place.
    time = datetime.strptime(
        f"{year:04}:{month:02}:{day:02}:{hh:02}:{mm:02}", "%Y:%m:%d:%H:%M"
    )
    return CxoTime(time, format="datetime").secs


@np.vectorize(otypes=[float])
def _att_factor(si, otg):
    """
    Determine instrument attenuation factor
    """
    att = 1
    if si in ("HRC-I", "HRC-S"):
        att = 0
    elif otg == "LETG":
        att = 0.5
    elif otg == "HETG":
        att = 0.2
    return att


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        choices=["flight", "test"],
        required=True,
        help="Determine running mode.",
    )
    parser.add_argument("-p", "--path", help="Determine data output file path")
    args = parser.parse_args()

    if args.mode == "test":
        if args.path:
            OUT_CRM_DATA_DIR = args.path
        else:
            OUT_CRM_DATA_DIR = f"{os.getcwd()}/test/_outTest"
        os.makedirs(OUT_CRM_DATA_DIR, exist_ok=True)

        create_crm_flux_table()

    elif args.mode == "flight":
        #
        # --- Create a lock file and exit strategy in case of race conditions.
        #
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            with open(f"/tmp/{user}/{name}.lock") as f:
                pid = int(f.readlines()[-1].strip())
                #: Kill old stalling process and remove corresponding lock file.
                os.remove(f"/tmp/{user}/{name}.lock")
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                #: Generate lock file for the current corresponding process
                os.system(
                    f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock"
                )
        else:
            #: Previous script run must have completed successfully. Prepare lock file for this script run.
            os.system(
                f"mkdir -p /tmp/{user}; echo '{os.getpid()}' > /tmp/{user}/{name}.lock"
            )

        create_crm_flux_table()
        #: Make data available on the web.
        os.system(
            f"cp {OUT_CRM_DATA_DIR}/crm_flux_table.ecsv {OUT_CRM_WEB_DIR}/crm_flux_table.ecsv"
        )
        if (
            os.stat(f"{OUT_CRM_DATA_DIR}/CRMarchive.ecsv").st_mtime
            > os.stat(f"{OUT_CRM_WEB_DIR}/CRMarchive.ecsv").st_mtime
        ):
            #: If archive has been modified recently, update available web copy.
            os.system(
                f"cp {OUT_CRM_DATA_DIR}/CRMarchive.ecsv {OUT_CRM_WEB_DIR}/CRMarchive.ecsv"
            )
        #
        # --- Remove lock file once process is completed.
        #
        os.system(f"rm /tmp/{user}/{name}.lock")
