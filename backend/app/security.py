"""
Security and authentication module for GeoAegis-ID.

Why Haversine Distance over Euclidean Distance?
-----------------------------------------------
Simple Euclidean distance (sqrt((x2 - x1)^2 + (y2 - y1)^2)) calculates straight-line distance on a 2D flat plane.
However, Earth is a 3D oblate spheroid. Applying Euclidean distance to latitude and longitude coordinates leads to
severe inaccuracy because:
1. Longitude lines converge at the poles (1 degree of longitude spans ~111 km at the equator, but shrinks to 0 km at the poles).
2. Straight 2D Euclidean lines cut through the Earth rather than following the Earth's curvature (Great Circle paths).

The Haversine formula accounts for spherical trigonometry on Earth's surface (approximating Earth radius R ≈ 6371 km),
providing accurate surface distance calculations across global GPS coordinates.
"""

import math
from datetime import datetime
from typing import Any, Dict, Union

EARTH_RADIUS_KM = 6371.0


def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometers
    using the Haversine formula.

    Why Haversine vs Euclidean:
    Euclidean distance assumes a flat 2D plane. Geographic coordinates (lat, lon) lie on Earth's curved
    surface where longitude lines converge at the poles. Haversine accounts for Earth's curvature,
    giving accurate surface distance in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def _extract_coord_and_time(login_data: Union[Dict[str, Any], Any]):
    """Helper to extract lat, lon, and timestamp from dictionary or object."""
    if isinstance(login_data, dict):
        lat = login_data.get("lat") if "lat" in login_data else login_data.get("latitude")
        lon = login_data.get("lon") if "lon" in login_data else login_data.get("longitude")
        ts = (
            login_data.get("timestamp")
            if "timestamp" in login_data
            else login_data.get("time")
        )
        if ts is None:
            ts = login_data.get("datetime")
    else:
        lat = getattr(login_data, "lat", getattr(login_data, "latitude", None))
        lon = getattr(login_data, "lon", getattr(login_data, "longitude", None))
        ts = getattr(
            login_data,
            "timestamp",
            getattr(login_data, "time", getattr(login_data, "datetime", None)),
        )

    if lat is None or lon is None or ts is None:
        raise ValueError("Login payload must include latitude, longitude, and timestamp.")

    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    elif isinstance(ts, datetime):
        ts = ts.timestamp()
    elif isinstance(ts, (int, float)):
        ts = float(ts)

    return float(lat), float(lon), ts


def is_impossible_travel(
    prev_login: Union[Dict[str, Any], Any],
    curr_login: Union[Dict[str, Any], Any],
    max_speed_kmh: float = 900.0,
) -> bool:
    """
    Determines if travel between two login events is physically impossible based on speed.

    Parameters:
        prev_login: Dict or object with lat/latitude, lon/longitude, and timestamp/time.
        curr_login: Dict or object with lat/latitude, lon/longitude, and timestamp/time.
        max_speed_kmh: Maximum realistic travel speed in km/h (default: 900 km/h for commercial aircraft).

    Returns:
        True if the required travel speed exceeds max_speed_kmh, False otherwise.
    """
    lat1, lon1, t1 = _extract_coord_and_time(prev_login)
    lat2, lon2, t2 = _extract_coord_and_time(curr_login)

    time_diff_hours = (t2 - t1) / 3600.0

    if time_diff_hours <= 0:
        # If time difference is zero or negative with distinct locations, speed is infinite
        distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        return distance > 0

    distance_km = calculate_haversine_distance(lat1, lon1, lat2, lon2)
    speed_kmh = distance_km / time_diff_hours

    return speed_kmh > max_speed_kmh
