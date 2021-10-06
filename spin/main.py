import logging

from spin import raspberrypi
from spin.database import db
from spin.config import config
from spin.workout import Workout

logger = logging.getLogger(__name__)


def start_smart_bike():
    """Start smart bike program."""
    logger.info("Program starting...")

    raspberrypi.setup()
    try:
        _main_loop()
    except KeyboardInterrupt:
        logger.info("Program terminated")
    except Exception as e:
        logger.exception(e)
    finally:
        _cleanup()


def _main_loop():
    while True:
        raspberrypi.wait_for_inputs([config["START_STOP_BUTTON_PIN"]])
        exercise = Workout()
        exercise.log_pedal_strokes()


def _cleanup():
    logger.debug("Cleaning up")
    raspberrypi.cleanup()
    db.cleanup()
