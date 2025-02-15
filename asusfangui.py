import sys
import os
import ctypes
import qdarkstyle  # Для красивой темной темы
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QDial, QGridLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

class AsusControl:
    def __init__(self):
        asus_dll.InitializeWinIo()

    def __del__(self):
        asus_dll.ShutdownWinIo()

    def set_fan_speed(self, percent, fan_index=0):
        value = int(percent / 100.0 * 255)
        asus_dll.HealthyTable_SetFanIndex(fan_index)
        asus_dll.HealthyTable_SetFanTestMode(ctypes.c_char(0x01 if value > 0 else 0x00))
        asus_dll.HealthyTable_SetFanPwmDuty(ctypes.c_short(value))

    def get_fan_count(self):
        return asus_dll.HealthyTable_FanCounts()

    def get_fan_speed(self, fan_index=0):
        asus_dll.HealthyTable_SetFanIndex(fan_index)
        return asus_dll.HealthyTable_FanRPM()

    def get_temperature(self, func_name):
        func = getattr(asus_dll, func_name, None)
        if func:
            return func()
        return 0

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asus Fan Control")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(400, 300)

        self.asus = AsusControl()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_fan_control_tab()
        self.init_temperature_tab()

    def init_fan_control_tab(self):
        fan_count = self.asus.get_fan_count()
        fan_tab = QWidget()
        layout = QGridLayout()

        self.fan_labels = []
        self.fan_dials = []

        for i in range(fan_count):
            fan_speed = self.asus.get_fan_speed(i)
            
            label = QLabel(f"Fan {i}: 0 RPM")
            dial = QDial()
            dial.setRange(0, 100)
            dial.setSingleStep(1)
            dial.valueChanged.connect(lambda value, idx=i: self.set_fan_speed(idx, value))

            layout.addWidget(label, i, 0)
            layout.addWidget(dial, i, 1)
            if fan_speed > 1000:
                dial.setValue(int(fan_speed / (8000 / 100)) if fan_speed < 7000 else 50)
            else:
                dial.setValue(50)

            self.fan_labels.append(label)
            self.fan_dials.append(dial)

        fan_tab.setLayout(layout)
        self.tabs.addTab(fan_tab, "Fans")

        self.fan_timer = QTimer(self)
        self.fan_timer.timeout.connect(self.update_fan_speeds)
        self.fan_timer.start(2000)

    def init_temperature_tab(self):
        self.temp_tab = QWidget()
        self.temp_layout = QVBoxLayout()

        self.temp_sensors = {
            "CPU": "Thermal_Read_Cpu_Temperature",
            "GPU Left": "Thermal_Read_GpuTS1L_Temperature",
            "GPU Right": "Thermal_Read_GpuTS1R_Temperature",
            "VRAM": "Thermal_Read_GpuVram_Temperature",
            "VRM": "Thermal_Read_GpuVrm_Temperature",
            "Board Left": "Thermal_Read_BoardTS0L_Temperature",
            "Board Right": "Thermal_Read_BoardTS0R_Temperature",
            "Charger": "Thermal_Read_ChargerChoke_Temperature"
        }

        self.temp_labels = {}
        for sensor, func in self.temp_sensors.items():
            label = QLabel(f"{sensor}: -- °C")
            self.temp_layout.addWidget(label)
            self.temp_labels[sensor] = label

        self.temp_tab.setLayout(self.temp_layout)
        self.tabs.addTab(self.temp_tab, "Temperatures")

        self.temp_timer = QTimer(self)
        self.temp_timer.timeout.connect(self.update_temperatures)
        self.temp_timer.start(3000)

    def set_fan_speed(self, fan_index, value):
        self.asus.set_fan_speed(value, fan_index)

    def update_fan_speeds(self):
        for i, label in enumerate(self.fan_labels):
            rpm = self.asus.get_fan_speed(i)
            label.setText(f"Fan {i}: {rpm} RPM")

    def update_temperatures(self):
        for sensor, func in self.temp_sensors.items():
            temp = self.asus.get_temperature(func)
            self.temp_labels[sensor].setText(f"{sensor}: {temp} °C")

if __name__ == "__main__":
    dll_path = os.path.abspath("AsusWinIO64.dll")
    asus_dll = ctypes.WinDLL(dll_path)
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())  # Тёмная тема
    window = MainWindow()
    window.show()
    app.exec()