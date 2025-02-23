from datetime import datetime
import logging

from pi_spin.database import Database
from pi_spin.raspberrypi import RaspberryPi

logger = logging.getLogger(__name__)


class Workout:
    """Represents a workout session."""

    def __init__(self, db: Database, raspberrypi: RaspberryPi):
        self.db = db
        self.raspberrypi = raspberrypi

        self.is_in_progress = False
        self.id = db.get_last_workout_id() + 1

    def start_workout(self):
        self.is_in_progress = True
        self.raspberrypi.turn_on_led()
        self.start_time = datetime.now()
        self.db.add_workout_start("default")

    def log_pedal_strokes(self):
        """Log each pedal stroke into database"""
        logger.info("Workout has begun. Logging in progress.")
        while True:
            event_channel = self.raspberrypi.wait_for_pedal_or_stop()
            if event_channel == self.raspberrypi.pedal_sensor_pin:
                self.db.add_pedal_entry(self.id)
            else:
                return

    def end_workout(self):
        """End current workout session."""
        logger.info("Workout is complete.")
        self.is_in_progress = False
        self.raspberrypi.turn_off_led()
        self.db.add_workout_end(self.id)
