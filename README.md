# pi-spin

pi-spin runs on a Raspberry Pi attached to a stationary bike. It records
workout sessions and individual pedal strokes in a local SQLite database.

Press the start/stop button to begin a workout (the LED turns on), pedal to
log strokes, and press the button again to end the session (the LED turns
off). The program then waits for the next workout. Stop it with Ctrl+C.

## Hardware

GPIO uses BOARD (physical pin) numbering, not BCM.
Defaults come from `src/pi_spin/conf/raspberry_pi.yaml`:

| Function           | BOARD pin | Direction | Behavior                                      |
| ------------------ | --------- | --------- | --------------------------------------------- |
| Pedal sensor       | 7         | Input     | Internal pull-up; rising edge logs a stroke   |
| Start/stop button  | 10        | Input     | Internal pull-up; rising edge starts or stops |
| Workout LED        | 8         | Output    | Driven high while a workout is in progress    |

Event detection uses a `bouncetime` of 200 (passed through to RPi.GPIO) and
polls every 0.1 seconds.

The repository does not document the sensor and button wiring.

## Raspberry Pi setup

The app is meant to run on Raspberry Pi OS (for example a headless Pi 3B
accessed over SSH). Python 3.10 or later is required.

It talks to GPIO directly. You do not need to enable I2C, SPI, or other
optional interfaces in `raspi-config`.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository and install the app, including the `pi` extra that
   pulls in `RPi.GPIO`:

   ```bash
   git clone https://github.com/rvforest/pi-spin.git
   cd pi-spin
   uv sync --extra pi
   ```

3. Your user needs permission to use GPIO. On Raspberry Pi OS that usually
   means membership in the `gpio` group:

   ```bash
   sudo usermod -aG gpio "$USER"
   ```

   Log out and back in (or reboot) so the group change takes effect.

Without the `pi` extra, a missing `RPi.GPIO` install is replaced by a mock, so
the program can start on a non-Pi machine but will not drive real hardware.

## Usage

Run the app from the directory where you want the database file created:

```bash
uv run pi-spin
```

`uv run python -m pi_spin` does the same thing. There are no command-line
options.

The program:

1. Waits for a rising edge on the start/stop button.
2. Turns the LED on and inserts a `WORKOUT` row (the user is always
   `default`).
3. Inserts a `PEDALING` row for each rising edge on the pedal sensor.
4. Turns the LED off and records the workout end when the start/stop button
   is pressed again, then returns to step 1.

Ctrl+C stops the program, turns the LED off, and releases GPIO. If a workout
was still open, an end time is written for it.

### Data and logging

Workouts are stored in `exercise.db` in the current working directory (the
file is gitignored). The database has two tables:

- `WORKOUT`: `id`, `user`, `begin`, `end`
- `PEDALING`: `id`, `workout_id`, `pedal_time`, and a `resistance` column
  reserved for a future enhancement

By default, logs go to the console at `INFO`. No log file is written unless
you change the logging config.

### Configuration

Packaged defaults live in `src/pi_spin/conf/`:

- `raspberry_pi.yaml` — GPIO pins, `bouncetime`, and `polling_delay`
- `sqlite.yaml` — database path (`exercise.db`), timestamp format, and
  connection options
- `logging.yaml` — log level, optional log file, console output, and format

## Development

On a machine without a Pi, omit the `pi` extra; tests mock GPIO.

```bash
uv sync
uv run pytest
```

[Nox](https://nox.thea.codes/) sessions (via `uv run nox -s <name>`):

- `lint` — `ruff check`
- `check_format` — `ruff format --check`
- `format` — `ruff format`
- `fix` — `ruff check --fix` and `ruff format`

Pre-commit hooks run zizmor and gitleaks:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## License

[MIT](LICENSE)
