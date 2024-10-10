import math
from datetime import datetime, timezone
from config import Config

PST = Config.get_timezone()

def calculate_parking_fee_and_time(entry_time, exit_time=None, rate_per_hour=50):

    if entry_time.tzinfo is None:
        entry_time_aware = entry_time.replace(tzinfo=timezone.utc)
    else:
        entry_time_aware = entry_time.astimezone(timezone.utc)

    exit_time_aware = exit_time if exit_time else datetime.now(timezone.utc)

    if exit_time_aware.tzinfo is None:
        exit_time_aware = exit_time_aware.replace(tzinfo=timezone.utc)
    else:
        exit_time_aware = exit_time_aware.astimezone(timezone.utc)

    duration = exit_time_aware - entry_time_aware
    hours_parked = math.ceil(duration.total_seconds() /  Config.SECONDS_PER_HOUR)
    parking_fee =  int(hours_parked * rate_per_hour) 

    entry_time_pst = entry_time_aware.astimezone(tz=PST)
    exit_time_pst = exit_time_aware.astimezone(tz=PST) 
    formatted_entry_time = entry_time_pst.strftime("%I:%M %p") 
    formatted_exit_time = exit_time_pst.strftime("%I:%M %p") if exit_time else None

    return formatted_entry_time, formatted_exit_time, parking_fee

