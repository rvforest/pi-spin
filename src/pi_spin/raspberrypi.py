"""Functions for handling all input/output from Raspberry Pi"""

import logging
import time
from typing import Iterable

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError as e:
    from unittest.mock import MagicMock
    GPIO = MagicMock()

from pi_spin.config import load_config

logger = logging.getLogger(__name__)


class RaspberryPi:
    def __init__(
        self,
        pedal_sensor_pin: int,
        start_stop_button_pin: int,
        led_pin: int,
        bouncetime: int,
        polling_delay: float,
    ):
        self.pedal_sensor_pin = pedal_sensor_pin
        self.start_stop_button_pin = start_stop_button_pin
        self.led_pin = led_pin
        self.bouncetime = bouncetime
        self.polling_delay = polling_delay

    @classmethod
    def from_config(
        cls, config_name: str = "raspberry_pi.yaml", config_pkg: str = "pi_spin.conf"
    ):
        config = load_config(config_name, config_pkg)
        logger.debug(config)
        return cls(**config)

    def setup(self):
        """Setup raspberry pi"""
        logger.info("Setting up raspberry pi...")
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.pedal_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.start_stop_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.led_pin, GPIO.OUT)

        GPIO.add_event_detect(
            self.pedal_sensor_pin, GPIO.RISING, bouncetime=self.bouncetime
        )
        GPIO.add_event_detect(
            self.start_stop_button_pin, GPIO.RISING, bouncetime=self.bouncetime
        )

    def _wait_for_inputs(self, channels: Iterable[int]) -> int:
        """
        Wait until input is received on one of the specified channels.

        GPIO.event_detected is used to ensure that events are not missed during loop sleep.

        :param channels:
        :param polling_delay:
        :return: Channel on which the event was detected.
        """
        logger.debug(f"Waiting for input on channels {channels}")
        while True:
            time.sleep(self.polling_delay)
            for channel in channels:
                if GPIO.event_detected(channel):
                    return channel

    def wait_for_start_button(self):
        return self._wait_for_inputs([self.start_stop_button_pin])

    def wait_for_pedal_or_stop(self):
        return self._wait_for_inputs(
            [self.start_stop_button_pin, self.pedal_sensor_pin]
        )

    def turn_on_led(self):
        """Turn on the LED"""
        GPIO.output(self.led_pin, GPIO.HIGH)

    def turn_off_led(self):
        """Turn off the LED"""
        GPIO.output(self.led_pin, GPIO.LOW)

    def cleanup(self):
        """Turn off LED and cleanup raspberry pi"""
        self.turn_off_led()
        GPIO.cleanup()
