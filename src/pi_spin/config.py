"""Load configuration then overwrite default with any user values."""

import importlib.resources
import logging
from pathlib import Path
from typing import Optional

import yaml


logger = logging.getLogger(__name__)


def load_config(
    config_name: str,
    config_pkg: str = "pi_spin.conf",
    user_conf_file: Optional[str] = None,
) -> dict:
    """Load a yaml configuration from package data.
    If a user config location is specified then user config will be loaded
    if it exists and the default config will be updated with values from user conf.

    Args:
        config_file (str): Config filename including .yaml extension.
        config_pkg (str): Package where config is located. Defaults to pi_spi.conf
        user_conf_file (Optional[str]): User config file path relative to user home.

    Returns:
        dict: Loaded config
    """
    # Load default config

    config_file = importlib.resources.files(config_pkg).joinpath(config_name)
    with config_file.open("r", encoding="utf-8") as f:
        conf_dict = yaml.safe_load(f)
        logger.info("Loaded default configuration")

    # Load user config values
    if user_conf_file:
        user_conf_path = Path.home().joinpath(user_conf_file)
        try:
            user_config_path = Path.home().joinpath(user_conf_path)
            with open(user_config_path, "r") as f:
                user_conf_dict = yaml.safe_load(f)
                logger.info("Loaded user configuration")
        except FileNotFoundError:
            user_conf_dict = {}
        conf_dict.update(user_conf_dict)

    return conf_dict
