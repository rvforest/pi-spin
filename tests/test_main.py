import threading
import time
from unittest import mock

import pytest

import pi_spin.main
from pi_spin.testing.mock_gpio import MockGPIO
from pi_spin.raspberrypi import RaspberryPi


@pytest.fixture
def mock_db():
    db_mock = mock.MagicMock()
    with mock.patch("pi_spin.database.Database", return_value=db_mock):
        yield db_mock


@pytest.fixture
def mock_gpio():
    with mock.patch("pi_spin.raspberrypi.GPIO", new=MockGPIO()) as gpio_mock:
        yield gpio_mock


@pytest.fixture
def mock_all_gpio_events(mock_gpio):
    """Return True every time we check for an event"""
    mock_gpio.event_detected = lambda channel: True
    return mock_gpio


def simulate_workout(mock_gpio, raspberrypi, n_pedals):
    # Wait for raspberrypi to be ready
    while raspberrypi.start_stop_button_pin not in mock_gpio.edge_detections:
        time.sleep(0.1)
    
    # Press button to start workout, pedal twice, then press button to stop workout
    mock_gpio.simulate_edge(raspberrypi.start_stop_button_pin, mock_gpio.RISING)
    for _ in range(n_pedals):
        time.sleep(1)
        mock_gpio.simulate_edge(raspberrypi.pedal_sensor_pin, mock_gpio.RISING)
    # Potential race condition since we need to wait for program to pick up last pedal
    # stroke before ending the workout.
    time.sleep(1)
    mock_gpio.simulate_edge(raspberrypi.start_stop_button_pin, mock_gpio.RISING)


def test_main(mock_db, mock_gpio):
    expected_n_pedals = 2

    # Create simulated workout
    raspberrypi = RaspberryPi.from_config()
    t = threading.Thread(
        target=simulate_workout,
        args=[mock_gpio, raspberrypi, expected_n_pedals],
        daemon=True,
    )
    t.start()

    # Mock device startup
    raspberrypi.setup()
    pi_spin.main._workout_loop(mock_db, raspberrypi)

    # Check that correct db entries are created
    mock_db.add_workout_start.assert_called_once()
    assert mock_db.add_pedal_entry.call_count == expected_n_pedals
    mock_db.add_workout_end.assert_called_once()
    