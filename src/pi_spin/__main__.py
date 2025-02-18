import logging
from multiprocessing import Process

from pi_spin.config import config
from pi_spin.main import start_smart_bike
from pi_spin.web_app.app import app

# Setup Logging
handlers = []
if config["LOG_FILE"] is not None:
    print(f'Added file handler for logging. File location: {config["LOG_FILE"]}')
    handlers.append(logging.FileHandler(config["LOG_FILE"]))
if config["LOG_TO_CONSOLE"] is not None:
    print("Adding stream handler for logging.")
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=getattr(logging, config["LOG_LEVEL"]),
    format="'%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
    handlers=handlers,
)

logging.debug(config)

# Run
pedal_logger = Process(target=start_smart_bike)
pedal_logger.start()
app.run_server(host=config["APP_HOST"])
