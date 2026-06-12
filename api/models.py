from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Measurement:
    id: int
    device_id: str
    measured_at: datetime
    value: float
    unit: str
    received_at: datetime

    def to_obj(self):
        return { 'id': self.id, 'device_id': self.device_id, 'value': self.value, 'unit': self.unit, 'timestamp': self.timestamp() }

    def timestamp(self):
        return datetime.fromtimestamp(self.measured_at, timezone.utc)

@dataclass
class TempMeasurement(Measurement):
    def to_obj(self):
        return { **super().to_obj(), 'type': 'temperature' }

@dataclass
class HumidMeasurement(Measurement):
    def to_obj(self):
        return { **super().to_obj(), 'type': 'humidity' }

@dataclass
class IlluminMeasurement(Measurement):
    def to_obj(self):
        return { **super().to_obj(), 'type': 'illumination' }

@dataclass
class SensorDevice:
    id: int
    device_id: str
    last_seen: datetime

    def to_obj(self):
        return {'id': self.id, 'device_id': self.device_id, 'last_seen': self.last_seen }
