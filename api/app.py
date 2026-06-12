import re

from flask import Flask, request, jsonify

from utils import ISODateJSONProvider

import db

storage = None 
app = Flask(__name__)
app.json_provider_class = ISODateJSONProvider(app)

@app.route("/")
def hello_world():
    return "<p>Testing testing testing</p>"

class Response():
    def __init__(self, ok, message):
        self._ok = ok
        self._message = message

    def to_obj(self):
        return { 'ok': self._ok, 'message': self._message }

    def to_json(self):
        return jsonify(self.to_obj())


class MeasurementsResponse(Response):
    def __init__(self, ok, message, measurements):
        super().__init__(ok, message)
        self._measurements = measurements

    def to_obj(self):
        return { **super().to_obj(), 'measurements': self._measurements }


class DevicesResponse(Response):
    def __init__(self, ok, message, devices):
        super().__init__(ok, message)
        self._devices = devices

    def to_obj(self):
        return { **super().to_obj(), 'devices': self._devices }


def process_args(args):
    devId = request.args.get('deviceId', None)
    limit = request.args.get('limit', 10)

    if devId is not None:
        if len(devId) > 32:
            devId = None

    try:
        limit = int(limit, 10)
    except Exception as e:
        limit = 10
    return (devId, limit)

@app.get("/temperature/v1")
def get_temperature():
    devId, limit = process_args(request.args)
    temps = [ t.to_obj() for t in storage.find_temperatures(devId, limit, latest=True) ]
    if temps is not None:
        return MeasurementsResponse(True, 'Success', temps).to_json()
    else:
        return Response(False, 'Error').to_json()


@app.get("/humidity/v1")
def get_humidity():
    devId, limit = process_args(request.args)
    temps = [ t.to_obj() for t in storage.find_humidities(devId, limit, latest=True) ]
    if temps is not None:
        return MeasurementsResponse(True, 'Success', temps).to_json()
    else:
        return Response(False, 'Error').to_json()


@app.get("/illumination/v1")
def get_illumination():
    devId, limit = process_args(request.args)
    temps = [ t.to_obj() for t in storage.find_illuminations(devId, limit, latest=True) ]
    if temps is not None:
        return MeasurementsResponse(True, 'Success', temps).to_json()
    else:
        return Response(False, 'Error').to_json()


@app.get("/devices/v1")
def get_devices():
    devices = storage.find_devices()
    if devices is not None:
        return DevicesResponse(True, 'Success', devices).to_json()
    else:
        return Response(False, 'Error').to_json()


@app.get("/health")
def get_health():
    return Response(True, 'Success').to_json()

#import routes.temperature

if __name__ == '__main__':
    storage = db.DatabaseConn()
    app.run(debug=True, host='0.0.0.0', port=5001)
