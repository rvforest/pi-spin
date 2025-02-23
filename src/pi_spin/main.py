import logging

from pi_spin.config import load_config
from pi_spin.raspberrypi import RaspberryPi
from pi_spin.database import Database
from pi_spin.workout import Workout

logger = logging.getLogger(__name__)


def start_smart_bike():
    """Start smart bike program."""
    _setup_logging()
    logger.info("Program starting...")
    db = Database.from_config()

    raspberrypi = RaspberryPi.from_config()
    raspberrypi.setup()
    try:
        _main_loop(db, raspberrypi)
    except KeyboardInterrupt:
        logger.info("Program terminated")
    except Exception as e:
        logger.exception(e)
    finally:
        logger.debug("Cleaning up")
        raspberrypi.cleanup()
        db.cleanup()


def _main_loop(db, raspberrypi):
    while True:
        raspberrypi.wait_for_start_button()
        exercise = Workout(db, raspberrypi)
        exercise.start_workout()
        exercise.log_pedal_strokes()
        exercise.end_workout()


def _setup_logging():
    config = load_config("logging.yaml")
    handlers = []
    if config["log_file"] is not None:
        handlers.append(logging.FileHandler(config["log_file"]))
    if config["log_to_console"] is not None:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, config["log_level"]),
        format=config["format"],
        handlers=handlers,
    )

    logging.debug(config)
