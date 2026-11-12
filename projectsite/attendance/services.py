import math
from django.utils import timezone


def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance in meters between two GPS coordinates
    using the Haversine formula.
    """
    R = 6371000.0  # Earth's mean radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(R * c, 2)


def evaluate_checkin_status(session, distance_m: float, check_time=None) -> str:
    """
    Determine attendance status ('present', 'late', or 'rejected')
    based on geofence radius and session time window.
    """
    if check_time is None:
        check_time = timezone.now()

    if distance_m > session.radius_m:
        return 'rejected'

    if check_time > session.late_after:
        return 'late'

    return 'present'