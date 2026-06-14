import sys
from urllib.parse import urljoin
from datetime import datetime

import pyqtgraph as pg
import numpy as np
import requests

from requests import ConnectionError
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QGroupBox, QCheckBox, QMessageBox,QListView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Slot, QTimer, QModelIndex

API_URL = 'http://localhost:5001/'

class DataContainer:
    def __init__(self, title, method, plot):
        self._title = title
        self._method = method
        self._plot = plot

        timer = QTimer()
        timer.setInterval(1000)
        timer.timeout.connect(self.on_timeout)
        self._timer = timer
        self._dev_id = None
        self._latest_ts = None
        self._x = np.empty((10,), dtype=float)
        self._y = np.empty((10,), dtype=float)
        self._len = 0
        self._axes = None

    def _fetch_data(self, limit):
        try:
            res = requests.get(urljoin(API_URL, self._method), {
                'limit': limit,
                'deviceId': self._dev_id
            })
            if res.status_code == 200:
                obj = res.json()
                if obj['ok']:
                    self._process_data(obj['measurements'])
        except ConnectionError:
            pass

    def _process_data(self, data):
        sz = len(data)
        if sz < 1:
            return
        ts = datetime.fromisoformat(data[0]['timestamp'])
        if self._latest_ts is not None and ts <= self._latest_ts:
            return

        if self._len + sz > 10:
            self._x[0:self._len-sz] = self._x[self._len-sz:self._len]
            self._y[0:self._len-sz] = self._y[self._len-sz:self._len]
            off = self._len - sz
        else:
            off = self._len
        if sz > 1:
            dt = None
            for i, datum in enumerate(reversed(data)):
                self._y[off+i] = datum['value']
                dt = datetime.fromisoformat(datum['timestamp'])
                self._x[off+i] = dt.timestamp()
            self._latest_ts = dt
        else:
            datum = data[0]
            self._y[off] = datum['value']
            dt = datetime.fromisoformat(datum['timestamp'])
            self._x[off] = dt.timestamp()
            self._latest_ts = dt
        self._len = (self._len + sz) % 10
        print(self._y)
        if self._axes is None:
            self._axes = self._plot.plot(self._x[0:self._len], self._y[0:self._len])
        else:
            self._axes.setData(self._x[0:self._len], self._y[0:self._len])

    def set_autorefresh(self, en):
        if self._dev_id is None:
            return
        if en:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def change_device(self, dev_id):
        self._dev_id = dev_id
        self._len = 0
        self._latest_ts = None
        if dev_id is not None:
            self._fetch_data(10)

    def update(self):
        if dev_it is not None:
            self._fetch_data(1)
    
    @Slot()
    def on_timeout(self):
        print(f'[{self._title}] TIMEOUT: Fetching new data')
        self._fetch_data(1)


class MainDialog(QDialog):
    def __init__(self):
        super().__init__()
        self._health_status = 0
        self._dev_id = None
        self.create_control_panel()
        self.create_plots()
        main_layout = QHBoxLayout()
        main_layout.addWidget(self._control_panel)
        main_layout.addWidget(self._plots)
        self.setLayout(main_layout)
        self.setWindowTitle("System Pomiarowy")

    def create_plots(self):
        gw = pg.GraphicsLayoutWidget()
        self._temp_plot = gw.addPlot(row=0, col=0)
        self._humid_plot = gw.addPlot(row=0, col=1)
        self._illum_plot = gw.addPlot(row=0, col=2)
        self._temp_data = DataContainer('Temperature', 'temperature/v1', self._temp_plot)
        self._humid_data = DataContainer('Humidity', 'humidity/v1', self._humid_plot)
        self._illum_data = DataContainer('Illumination', 'illumination/v1', self._illum_plot)
        self._containers = [ self._temp_data, self._humid_data, self._illum_data ]
        self._plots = gw

    def create_control_panel(self):
        self._control_panel = QGroupBox("Control")
        layout = QVBoxLayout()
        hc_btn = QPushButton("Healtcheck")
        hc_btn.clicked.connect(self.do_healthcheck)
        layout.addWidget(hc_btn)
        self._health_label = QLabel("Status: ???")
        layout.addWidget(self._health_label)
        devices_view = QListView(self)
        devices_view.clicked.connect(self.on_device_changed)
        devices = QStandardItemModel()
        devices_view.setModel(devices)
        layout.addWidget(devices_view)
        self._devices = devices
        fetch_devices = QPushButton("Refresh Devices")
        fetch_devices.clicked.connect(self.do_fetch_devices)
        layout.addWidget(fetch_devices)
        autorefresh = QCheckBox("Auto-update")
        autorefresh.stateChanged.connect(self.on_autorefresh_checked)
        self._autorefresh = autorefresh
        layout.addWidget(autorefresh)
        update = QPushButton("Update")
        update.clicked.connect(self.do_update)
        layout.addWidget(update)
        self._update_health()
        self._control_panel.setLayout(layout)

    def _update_health(self):
        if self._health_status == 0: 
            status = "???"
        elif self._health_status == 1:
            status = "OK"
        else:
            status = "DOWN"
        self._health_label.setText("Status: " + status)
        
    @Slot()
    def do_healthcheck(self):
        try:
            res = requests.get(urljoin(API_URL, '/health'))
            if res.status_code == 200:
                if res.json()['ok']:
                    self._health_status = 1
            else:
                self._health_status = 2
        except ConnectionError:
            self._health_status = 2
        self._update_health()

    @Slot()
    def on_autorefresh_checked(self):
        autorefresh = self._autorefresh.isChecked()
        if autorefresh and self._dev_id is None:
            self._autorefresh.setChecked(False)
            QMessageBox.warning(self, "Warning", "No device id selected")
            return
        print(f"Autorefresh {autorefresh}")
        for container in self._containers:
            container.set_autorefresh(autorefresh)

    @Slot()
    def do_fetch_devices(self):
        try:
            res = requests.get(urljoin(API_URL, '/devices/v1'))
            if res.status_code == 200:
                obj = res.json()
                if obj['ok']:
                    print(obj['devices'])
                    self._devices.clear()
                    for dev in obj['devices']:
                        self._devices.appendRow(QStandardItem(dev['device_id']))
                else:
                    QMessageBox.error(self, "Error", f"Failed to refresh the device list: Response is not ok")
            else:
                QMessageBox.error(self, "Error", f"Failed to refresh the device list: Server returned {res.status_code}")
        except ConnectionError as e:
            QMessageBox.error(self, "Error", f"Failed to refresh the device list: {e}")

    @Slot()
    def do_update(self):
        for container in self._containers:
            container.update()

    @Slot(QModelIndex)
    def on_device_changed(self, index):
        print(f"Device changed: {index.data()}")
        self._dev_id = index.data()
        for container in self._containers:
            container.change_device(index.data())

@Slot()
def say_hello():
    print("Button clicked, Hello!")

app = QApplication(sys.argv)
dialog = MainDialog()
dialog.show()
app.exec()
