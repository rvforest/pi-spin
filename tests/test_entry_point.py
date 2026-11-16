from importlib.metadata import entry_points

from pi_spin.main import start_smart_bike


def test_console_script_entry_point_loads_start_smart_bike():
    scripts = entry_points(group="console_scripts")
    ep = next(script for script in scripts if script.name == "pi-spin")
    loaded = ep.load()
    assert loaded is start_smart_bike
    assert callable(loaded)
