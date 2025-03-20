import threading
from unittest.mock import MagicMock


class MockGPIO(MagicMock):
    BCM = "BCM"
    BOARD = "BOARD"
    IN = "IN"
    OUT = "OUT"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    RISING = "RISING"
    FALLING = "FALLING"
    BOTH = "BOTH"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pins = {}
        self.edge_detections = {}
        self.waiting_threads = {}

    def setup(self, pin, direction, pull_up_down=None):
        self.pins[pin] = {"direction": direction, "pull": pull_up_down, "value": 0}

    def wait_for_edge(self, pin, edge_type):
        event = threading.Event()
        self.waiting_threads[pin] = event
        event.wait()  # Blocks until edge is triggered
        return pin

    def add_event_detect(self, pin, edge_type, bouncetime, callback=None):
        self.edge_detections[pin] = {
            "edge_type": edge_type,
            "bouncetime": bouncetime,
            "callback": callback,
            "detected": False,
        }

    def event_detected(self, pin) -> bool:
        result = self.edge_detections[pin]["detected"]
        self.edge_detections[pin]["detected"] = False
        return result

    def simulate_edge(self, pin, edge_type):
        """Manually triggers an edge detection"""
        if pin in self.pins and self.pins[pin]["direction"] == self.IN:
            self._trigger_edge(pin, edge_type)

    def _trigger_edge(self, pin, edge_type):
        if pin in self.edge_detections:
            detector_edge_type = self.edge_detections[pin]["edge_type"]
            if (edge_type == detector_edge_type) or (detector_edge_type == self.BOTH):
                callback = self.edge_detections[pin]["callback"]
                if callback:
                    threading.Thread(target=callback, args=(pin,)).start()
                self.edge_detections[pin]["detected"] = True

        if pin in self.waiting_threads:
            self.waiting_threads[pin].set()  # Unblock `wait_for_edge`

    def cleanup(self):
        self.pins.clear()
        self.edge_detections.clear()
        self.waiting_threads.clear()
