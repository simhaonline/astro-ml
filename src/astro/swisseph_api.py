import swisseph as swe
import pandas as pd
import numpy as np
from datetime import datetime

swe.set_ephe_path(None)

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "MeanNode": swe.MEAN_NODE,
}

def utc_julian(dt: pd.Timestamp) -> float:
    return swe.utc_to_jd(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)[1]

def build_ephemeris(dates: pd.DatetimeIndex, ayanamsa: str = "Lahiri") -> pd.DataFrame:
    swe.set_sid_mode(getattr(swe, f"SIDM_LAHIRI"))
    rows = []
    for dt in dates:
        jd = utc_julian(dt)
        row = {"datetime": dt}
        for name, pid in PLANETS.items():
            xx, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            row[f"{name}_long"] = xx[0] % 360
            row[f"{name}_lat"] = xx[1]
            row[f"{name}_speed"] = xx[3]
        cusps, ascmc = swe.houses(jd, 0, 0, b"P")
        for i in range(12):
            row[f"House_{i+1}"] = cusps[i] % 360
        row["Asc"] = ascmc[0]
        row["MC"] = ascmc[1]
        rows.append(row)
    return pd.DataFrame(rows).set_index("datetime")
