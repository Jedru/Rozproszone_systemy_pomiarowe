import psycopg
from psycopg.types.enum import EnumInfo, register_enum
from psycopg.rows import class_row

import config
from models import TempMeasurement, HumidMeasurement, IlluminMeasurement, SensorDevice

class DatabaseConn:
    def __init__(self):
        self._conn = psycopg.connect(f"host={config.DB_HOST} dbname={config.DB_NAME} user={config.DB_USER} password={config.DB_PASSWORD}")


    def _generate_query(self, sensor, dev_id, limit, latest):
        query = "SELECT id, device_id, value, unit, ts_ms AS measured_at, received_at FROM measurements AS m "
        query += f"WHERE m.sensor = '{sensor}'"
        if dev_id is not None:
            query += f"AND m.device_id = '{dev_id}' "
        if latest:
            query += "ORDER BY m.ts_ms DESC "
        else:
            query += "ORDER BY m.ts_ms ASC "
        if limit > 0:
            query += f"LIMIT {limit} "
        return query


    def find_temperatures(self, dev_id, limit, latest=True):
        try:
            with self._conn.cursor(row_factory=class_row(TempMeasurement)) as cur:
                cur.execute(self._generate_query('temperature', dev_id, limit, latest))
                return cur.fetchall()
        except Error:
            return None

    def find_humidities(self, dev_id, limit, latest=True):
        try:
            with self._conn.cursor(row_factory=class_row(HumidMeasurement)) as cur:
                cur.execute(self._generate_query('humidity', dev_id, limit, latest))
                return cur.fetchall()
        except Error:
            return None

    def find_illuminations(self, dev_id, limit, latest=True):
        try:
            with self._conn.cursor(row_factory=class_row(IlluminMeasurement)) as cur:
                cur.execute(self._generate_query('illumination', dev_id, limit, latest))
                return cur.fetchall()
        except Error:
            return None

    def find_devices(self):
        try:
            with self._conn.cursor(row_factory=class_row(SensorDevice)) as cur:
                query = "select row_number() OVER (ORDER BY 1) AS id, device_id, to_timestamp(max(ts_ms)) AS last_seen FROM measurements AS m GROUP BY device_id"
                cur.execute(query);
                return cur.fetchall()
        except Error as e:
            return None
