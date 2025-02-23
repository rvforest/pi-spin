"""Functions for handling all input/output from Raspberry Pi"""

import logging
import time
from typing import Iterable

import RPi.GPIO as GPIO

from pi_spin.config import config

logger = logging.getLogger(__name__)


def setup():
    """Setup raspberry pi"""
    logger.info("Setting up raspberry pi...")
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(config["PEDAL_SENSOR_PIN"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(config["START_STOP_BUTTON_PIN"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(config["LED_PIN"], GPIO.OUT)

    GPIO.add_event_detect(config["PEDAL_SENSOR_PIN"], GPIO.RISING, bouncetime=200)
    GPIO.add_event_detect(config["START_STOP_BUTTON_PIN"], GPIO.RISING, bouncetime=200)


def wait_for_inputs(channels: Iterable[int], polling_delay=0.1) -> int:
    """
    Wait until input is received on one of the specified channels.

    GPIO.event_detected is used to ensure that events are not missed during loop sleep.

    :param channels:
    :param polling_delay:
    :return: Channel on which the event was detected.
    """
    logger.debug(f"Waiting for input on channels {channels}")
    while True:
        time.sleep(polling_delay)
        for channel in channels:
            if GPIO.event_detected(channel):
                return channel


def turn_on_led():
    """Turn on the LED"""
    GPIO.output(config["LED_PIN"], GPIO.HIGH)


def turn_off_led():
    """Turn off the LED"""
    GPIO.output(config["LED_PIN"], GPIO.LOW)


def cleanup():
    """Turn off LED and cleanup raspberry pi"""
    turn_off_led()
    GPIO.cleanup()
