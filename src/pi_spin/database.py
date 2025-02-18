import logging
import sqlite3
from typing import List, Tuple, Any, Optional

from pi_spin.config import config

logger = logging.getLogger(__name__)

Data = List[Any]
ColumnNames = List[str]

WORKOUT_PK_COL = 0
WORKOUT_END_COL = 3
PEDAL_TIME_COL = 2


class Database:
    """Handles reading and writing from sqlite database"""

    # SQLite datetime format string
    dt_format = "%Y-%m-%d %H:%M:%f"

    def __init__(self):
        self.conn = sqlite3.connect(config["DB_FILE"], check_same_thread=False)
        self._make_tables()

    def execute_sql(self, sql: str) -> Tuple[List[Any], ColumnNames]:
        """Execute SQL statement then retrieve all results"""
        logger.debug(f"Executing: {sql}")
        c = self.conn.cursor()
        data = c.execute(sql).fetchall()

        # Get column names if applicable
        if c.description is not None:
            cols = [col[0] for col in c.description]
        else:
            cols = None

        self.conn.commit()
        c.close()

        return data, cols

    def close(self):
        """Close SQLite connection"""
        self.conn.close()

    def _make_tables(self):
        """If tables do not exist in database then create them."""

        # Default NOW value for datetime columns allow SQLite to handle entry instead of Python
        self.execute_sql(
            f"""
            CREATE TABLE IF NOT EXISTS WORKOUT (
                id INTEGER PRIMARY KEY,
                user TEXT NOT NULL,
                begin DATETIME NOT NULL DEFAULT(STRFTIME('{Database.dt_format}', 'NOW', 'localtime')),
                end DATETIME DEFAULT(STRFTIME('{Database.dt_format}', 'NOW', 'localtime'))
            ); 
            """
        )

        # Resistance column is a placeholder for future enhancement to log bike resistance.
        self.execute_sql(
            f"""
            CREATE TABLE IF NOT EXISTS PEDALING (
                id INTEGER PRIMARY KEY,
                workout_id INTEGER NOT NULL,
                pedal_time DATETIME NOT NULL DEFAULT(STRFTIME('{Database.dt_format}', 'NOW', 'localtime')),
                resistance REAL
            ); 
            """
        )

    def get_last_workout_id(self) -> int:
        """Get the ID of the last workout entered into the database"""
        last_workout = self.get_last_workout()
        if last_workout is None:
            last_id = 0
        else:
            last_id = last_workout[WORKOUT_PK_COL]
        return last_id

    def add_pedal_entry(self, workout_id: int):
        """
        Add entry with workout id and current timestamp. SQLite will automatically add the timestamp.
        """
        self.execute_sql(f"INSERT INTO PEDALING (workout_id) VALUES ({workout_id})")

    def add_workout_start(self, user: str):
        """Start a new workout in the database. Enters all fields except `end`."""
        self.execute_sql(f"INSERT INTO WORKOUT (user, end) VALUES ('{user}', NULL)")

    def add_workout_end(self, workout_id: int):
        """Add current time as `end` value for specified workout"""
        self.execute_sql(
            f"REPLACE INTO WORKOUT (id, user, begin) SELECT id, user, begin FROM WORKOUT WHERE id={workout_id}"
        )

    def get_last_workout(self) -> Optional[Data]:
        result, _ = self.execute_sql("SELECT * FROM WORKOUT ORDER BY id DESC LIMIT 1;")
        try:
            return result[0]
        except IndexError:
            return None

    def cleanup(self):
        """Clean up workout table then close connection"""
        # If workout was in progress at shutdown, then add an end time for this workout
        last_workout = self.get_last_workout()
        if last_workout is not None:
            end_time = last_workout[-1]
            if end_time is None:
                last_id = last_workout[WORKOUT_PK_COL]
                self.add_workout_end(last_id)
        self.close()

    def get_workout_list(self) -> Tuple[Data, ColumnNames]:
        return self.execute_sql("SELECT * FROM WORKOUT")

    def get_workout_log(
        self, workout_id, start_time_filter=None
    ) -> Tuple[Data, ColumnNames]:
        if start_time_filter is not None:
            time_filter = f"AND pedal_time >= '{start_time_filter}'"
        else:
            time_filter = ""
        return self.execute_sql(
            f"SELECT * FROM PEDALING WHERE workout_id = {workout_id} {time_filter}"
        )


db = Database()
