"""Load configuration then overwrite default with any user values."""

from pathlib import Path

import yaml


def load_config():
    # Load default config
    print("Loading default configuration")
    config_filename = ".smart_bike_conf.yaml"
    with open(config_filename, "r") as f:
        c = yaml.safe_load(f)

    # Load user config values
    try:
        user_config_path = Path.home().joinpath(config_filename)
        with open(user_config_path, "r") as f:
            c.update(yaml.safe_load(f))
        print("Loading user configuration")
    except FileNotFoundError:
        pass

    return c


config = load_config()
