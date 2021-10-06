from datetime import datetime
import logging

from spin.database import db
from spin.config import config
from spin import raspberrypi

logger = logging.getLogger(__name__)


class Workout:
    """Represents a workout session."""

    def __init__(self):
        last_id = db.get_last_workout_id()
        self.id = last_id + 1
        self.is_in_progress = True
        raspberrypi.turn_on_led()
        self.start_time = datetime.now()
        db.add_workout_start("default")

    def log_pedal_strokes(self):
        """Log each pedal stroke into database"""
        logger.info("Workout has begun. Logging in progress.")
        while True:
            event_channel = raspberrypi.wait_for_inputs(
                [config["PEDAL_SENSOR_PIN"], config["START_STOP_BUTTON_PIN"]]
            )
            if event_channel == config["PEDAL_SENSOR_PIN"]:
                db.add_pedal_entry(self.id)
            else:
                self.end()
                return

    def end(self):
        """End current workout session."""
        logger.info("Workout is complete.")
        self.is_in_progress = False
        raspberrypi.turn_off_led()
        db.add_workout_end(self.id)
