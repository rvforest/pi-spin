from datetime import datetime
from typing import Iterable, Tuple

import numpy as np

from pi_spin.config import config
from pi_spin.database import PEDAL_TIME_COL


def parse_date_string(date_string: str) -> datetime:
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")


def parse_dates(new_log_entries: Iterable[str]) -> np.ndarray:
    new_pedal_times = np.array(
        [entry[PEDAL_TIME_COL] for entry in new_log_entries], dtype=np.datetime64
    )
    return new_pedal_times


def calculate_time_delta(pedal_times: np.ndarray) -> np.ndarray:

    if len(pedal_times) <= 1:
        return np.zeros(1)

    delta_t = np.roll(pedal_times, -1) - pedal_times
    # Last entry is meaningless so remove it. Convert from ms to s
    return delta_t.astype(float)[:-1] / 1000


def calculate_rpm(pedal_times: np.ndarray) -> np.ndarray:
    delta_t = calculate_time_delta(pedal_times)
    rpm = 60 / delta_t
    return rpm


def add_rest_periods(
    pedal_times: np.ndarray, rpm: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    If no pedal strokes are detected for longer than pedal_timeout
    then assume pedaling has stopped and add entries with zero rpm
    """
    pedaling_timeout = config["PEDALING_TIMEOUT"]

    # When time between pedal strokes exceeds the pedal_timeout, then add zeros to the rpm array
    # Assume that pedaling is in progress before the timeout period. Split the in progress pedaling
    # between the start and end of the rest period
    delta_t = calculate_time_delta(pedal_times)
    is_at_rest = delta_t >= pedaling_timeout
    time_at_start_of_rest = pedal_times[:-1][is_at_rest] + round(
        1000 * pedaling_timeout / 2
    )
    time_at_end_of_rest = pedal_times[1:][is_at_rest] - round(
        1000 * pedaling_timeout / 2
    )

    pedal_times = np.concatenate(
        [pedal_times[1:], time_at_start_of_rest, time_at_end_of_rest]
    )
    n_new_entries = len(time_at_start_of_rest) + len(time_at_end_of_rest)
    rpm = np.concatenate([rpm, np.zeros(n_new_entries)])

    # Sort in chronological order
    sorted_idx = pedal_times.argsort()
    pedal_times = pedal_times[sorted_idx]
    rpm = rpm[sorted_idx]

    return pedal_times, rpm
