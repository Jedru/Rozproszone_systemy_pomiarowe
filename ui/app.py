from flask import Flask, render_template, jsonify
import requests
from collections import defaultdict
from datetime import datetime

API_BASE = 'http://localhost:5001/measurements'
TIMEOUT = 4

app = Flask(__name__)


def fmt_ts(ts_ms):
    try:
        return datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return '—'


def normalize(items):
    out = []
    for item in items or []:
        out.append({
            'id': item.get('id'),
            'group_id': item.get('group_id') or '—',
            'device_id': item.get('device_id') or 'unknown',
            'sensor': item.get('sensor') or 'unknown',
            'value': item.get('value'),
            'unit': item.get('unit') or '',
            'ts_ms': item.get('ts_ms'),
            'seq': item.get('seq'),
            'topic': item.get('topic') or '—',
            'ts_readable': fmt_ts(item.get('ts_ms', 0)),
        })
    return out


def fetch_measurements():
    resp = requests.get(API_BASE, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        if 'items' in data and isinstance(data['items'], list):
            return normalize(data['items'])
        if 'data' in data and isinstance(data['data'], list):
            return normalize(data['data'])
        return normalize([data])
    return normalize(data)


def fetch_latest():
    resp = requests.get(f'{API_BASE}/latest', timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return normalize(data)
    if isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
        return normalize(data['items'])
    return normalize([data])


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/dashboard')
def dashboard_data():
    result = {
        'connection': {
            'api_active': False,
            'mqtt_active': False,
            'message': 'Brak połączenia z API.',
        },
        'summary': {
            'temperature': None,
            'humidity': None,
            'pressure': None,
            'device_id': '—',
            'group_id': '—',
            'topic': '—',
            'last_update': '—'
        },
        'latest_rows': [],
        'series': {
            'temperature': [],
            'humidity': [],
            'pressure': []
        }
    }
    try:
        all_rows = fetch_measurements()
        latest_rows = fetch_latest()
        result['connection']['api_active'] = True
        result['connection']['mqtt_active'] = len(all_rows) > 0
        result['connection']['message'] = 'API odpowiada. Strumień danych wygląda na aktywny.' if all_rows else 'API odpowiada, ale brak pomiarów.'
        result['latest_rows'] = latest_rows

        sensor_aliases = {
            'temperature': 'temperature',
            'temp': 'temperature',
            'humidity': 'humidity',
            'wilgotnosc': 'humidity',
            'pressure': 'pressure',
            'cisnienie': 'pressure',
            'bmp280_temperature': 'temperature',
            'bmp280_humidity': 'humidity',
            'bmp280_pressure': 'pressure',
            'bme280_temperature': 'temperature',
            'bme280_humidity': 'humidity',
            'bme280_pressure': 'pressure'
        }

        grouped = defaultdict(list)
        for row in sorted(all_rows, key=lambda x: x.get('ts_ms') or 0):
            sensor_key = str(row.get('sensor', '')).lower().strip()
            mapped = sensor_aliases.get(sensor_key)
            if mapped:
                grouped[mapped].append({
                    'x': row['ts_readable'],
                    'y': row.get('value'),
                    'device_id': row.get('device_id'),
                    'topic': row.get('topic')
                })

        for key in ['temperature', 'humidity', 'pressure']:
            result['series'][key] = grouped[key][-80:]

        latest_map = {}
        for row in latest_rows:
            sensor_key = str(row.get('sensor', '')).lower().strip()
            mapped = sensor_aliases.get(sensor_key)
            if mapped:
                latest_map[mapped] = row

        for key in ['temperature', 'humidity', 'pressure']:
            row = latest_map.get(key)
            if row:
                result['summary'][key] = {
                    'value': row.get('value'),
                    'unit': row.get('unit')
                }
                result['summary']['device_id'] = row.get('device_id') or result['summary']['device_id']
                result['summary']['group_id'] = row.get('group_id') or result['summary']['group_id']
                result['summary']['topic'] = row.get('topic') or result['summary']['topic']
                result['summary']['last_update'] = row.get('ts_readable') or result['summary']['last_update']

    except Exception as exc:
        result['connection']['message'] = f'Błąd odczytu danych: {exc}'

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5055)
