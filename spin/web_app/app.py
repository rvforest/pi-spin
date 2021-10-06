from datetime import datetime, timedelta
import json
import logging

import numpy as np
from dash import Dash, html, dcc
from dash.exceptions import PreventUpdate
import dash_daq as daq
import plotly.express as px
from dash.dependencies import Input, Output, State

from spin.config import config
from spin.database import Database, WORKOUT_END_COL, WORKOUT_PK_COL, PEDAL_TIME_COL
from spin.web_app.data_processing import calculate_rpm, add_rest_periods, parse_dates

logger = logging.getLogger(__name__)

IN_PROGRESS = None  # None value on end column indicates in progress workout

db = Database()
no_data = json.dumps({"time": [], "rpm": [], "id": []})

app = Dash(__name__)
app.layout = html.Div(
    html.Div(
        [
            html.H1("PiSpin"),
            html.Div(id="live-update-text"),
            daq.Gauge(
                id="speed-gauge",
                showCurrentValue=True,
                min=0,
                max=200,
                units="RPM",
                value=0,
                color={
                    "gradient": True,
                    "ranges": {
                        "green": [0, 70],
                        "yellow": [70, 140],
                        "red": [140, 200],
                    },
                },
            ),
            dcc.Graph(id="live-update-graph"),
            dcc.Interval(
                id="interval-component",
                interval=config['APP_UPDATE_INTERVAL'] * 1000,  # in milliseconds
                n_intervals=0,
            ),
            dcc.Store(id="pedal-data", data=no_data),
        ]
    )
)


@app.callback(
    Output("pedal-data", "data"),
    Input("interval-component", "n_intervals"),
    State("pedal-data", "data"),
)
def update_data_store(n, pedaling_json: str):
    """
    Update data store with new data from SQLite.
    :param n:
    :param pedaling_json:
    :return:
    """
    logger.debug("Inside update_data_store")

    if n == 0:
        raise PreventUpdate

    now = datetime.now()
    if n == 1:
        last_interval = None
    else:
        last_interval = now - timedelta(seconds=config['APP_UPDATE_INTERVAL'])

    old_data = json.loads(pedaling_json)

    # Get new data since last logged pedal stroke
    last_workout = db.get_last_workout()
    workout_is_in_progress = (last_workout is not None) and (
        last_workout[WORKOUT_END_COL] is IN_PROGRESS
    )
    if not workout_is_in_progress:
        logger.debug("No workout in progress")
        return no_data

    logger.debug("workout in progress. Getting latest pedaling events")

    new_log_entries, _ = db.get_workout_log(
        last_workout[WORKOUT_PK_COL], start_time_filter=last_interval
    )
    logger.debug(f"New log entries: {new_log_entries}")

    new_log_entries = [
        entry for entry in new_log_entries if entry[0] not in old_data["id"]
    ]

    has_new_pedals = len(new_log_entries) > 0
    can_calculate_rpm = (len(new_log_entries) >= 2) or (
        (len(new_log_entries) == 1) and (len(old_data["rpm"]) > 0)
    )
    logger.debug(f"Has new data: {has_new_pedals}")
    logger.debug(f"Can calculate new rpm: {can_calculate_rpm}")
    if not has_new_pedals:
        return pedaling_json
    elif not can_calculate_rpm:
        # If only a single pedal has been logged, rpm cannot be calculated
        # We still need to return the new pedal event so rpm can be calculated on the next stroke
        time_str = new_log_entries[0][PEDAL_TIME_COL].replace(" ", "T")
        return json.dumps(
            {"time": [time_str], "rpm": [0], "id": [new_log_entries[0][0]]}
        )

    ids = [entry[0] for entry in new_log_entries]
    new_pedal_times = parse_dates(new_log_entries)

    # Add last entry from old data so that rpm can be calculated
    has_old_data = len(old_data["time"]) > 0
    if has_old_data:
        last_entry = np.array([old_data["time"][-1]], dtype=np.datetime64)
        new_pedal_times = np.concatenate([last_entry, new_pedal_times])
    logger.debug(f"Pedal times used for RPM calc: {new_pedal_times}")

    # Process new data
    rpm = calculate_rpm(new_pedal_times)
    logger.debug(f"New RPM values: {rpm}")

    new_pedal_times, rpm = add_rest_periods(new_pedal_times, rpm)
    logger.debug(f"New pedal_time values after rest periods: {new_pedal_times}")
    logger.debug(f"New RPM values after rest periods: {rpm}")

    new_pedal_times = new_pedal_times.astype(str)

    # Concatenate new data to old data
    all_data = {
        "time": np.concatenate([old_data["time"], new_pedal_times]).tolist(),
        "rpm": np.concatenate([old_data["rpm"], rpm]).tolist(),
        "id": ids,
    }

    # Send to Store
    return json.dumps(all_data)


@app.callback(Output("live-update-graph", "figure"), Input("pedal-data", "data"))
def update_figure(data):
    logger.debug("inside update_figure")

    if not data:
        raise PreventUpdate

    data = json.loads(data)
    pedal_time = np.array(data["time"], dtype=np.datetime64)
    rpm = data["rpm"]

    # If timeout has expired then make rpm zero
    if len(data["time"]) > 0:
        now = datetime.now()
        last_pedal = datetime.strptime(data["time"][-1], "%Y-%m-%dT%H:%M:%S.%f")
        time_since_last_pedal = now - last_pedal
        if time_since_last_pedal.total_seconds() >= config["PEDALING_TIMEOUT"]:
            # noinspection PyTypeChecker
            pedal_time = np.append(
                pedal_time, last_pedal + timedelta(seconds=config["PEDALING_TIMEOUT"])
            )
            # noinspection PyTypeChecker
            pedal_time = np.append(pedal_time, now)
            rpm += [0.0, 0.0]

    if len(pedal_time) > 0:
        return px.line(x=pedal_time, y=rpm)
    else:
        return None


@app.callback(Output("speed-gauge", "value"), Input("pedal-data", "data"))
def update_speed_gauge(data):
    logger.debug("Inside update_speed_gauge")
    if not data:
        raise PreventUpdate

    data = json.loads(data)
    rpm = data["rpm"]
    if len(rpm) == 0:
        return 0

    last_pedal = datetime.strptime(data["time"][-1], "%Y-%m-%dT%H:%M:%S.%f")
    time_since_last_pedal = datetime.now() - last_pedal

    if time_since_last_pedal.total_seconds() >= config["PEDALING_TIMEOUT"]:
        return 0

    return rpm[-1]


if __name__ == "__main__":
    try:
        app.run_server(host=config["APP_HOST"])
    finally:
        db.close()
