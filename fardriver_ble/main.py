import sys
import asyncio
from bleak import BleakScanner
from PyQt6.QtCore import Qt, QMimeData, QTimer, QRect
from PyQt6.QtGui import QDrag, QFontMetrics
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QListWidget, QListWidgetItem, QFrame, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QScrollArea, QSplitter, QPlainTextEdit, QSizePolicy
from qasync import QEventLoop
from fd import Fd
from bledev import Bledev
UUID = "0000ffec-0000-1000-8000-00805f9b34fb"
DEVICE_NAME = "YuanQuFOC298"
SENSORS = {
    "battery_voltage": ("Battery Voltage", "V"),
    "line_current": ("Line Current", "A"),
    "battery_power": ("Battery Power", "W"),
    "motor_temperature": ("Motor Temperature", "°C"),
    "controller_temperature": ("Controller Temperature", "°C"),
    "battery_soc_raw": ("Battery SOC (raw)", ""),
    "throttle_depth_raw": ("Throttle (raw)", ""),
    "measured_speed_raw": ("Speed (raw)", ""),
    "gear": ("Gear", ""),
    "gear_raw": ("Gear (raw)", ""),
    "direction": ("Direction", ""),
    "forward": ("Forward", ""),
    "reverse": ("Reverse", ""),
    "brake": ("Brake", ""),
    "moving": ("Moving", ""),
    "sliding_backwards": ("Sliding Backward", ""),
    "modulation": ("Modulation", ""),
    "warnings": ("Warnings", ""),
    "fault_mask": ("Fault Mask", ""),
    "controller_flags": ("Controller Flags", ""),
    "input_diagnostics": ("Input Diagnostics", ""),
    "configured_pin_selectors": ("Pin Selectors", ""),
    "rated_voltage": ("Rated Voltage", "V"),
    "max_line_current": ("Max Line Current", "A"),
    "max_phase_current": ("Max Phase Current", "A"),
    "low_voltage_cutoff": ("Low Voltage Cutoff", "V"),
    "high_voltage_cutoff": ("High Voltage Cutoff", "V"),
    "pole_pairs": ("Pole Pairs", "")
}
def display_value(key, value):
    if value is None:
        return "--"
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    if key == "fault_mask" and isinstance(value, int):
        return f"0x{value:04X}"
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items()) or "None"
    if isinstance(value, (tuple, list)):
        return ", ".join(map(str, value)) or "None"
    unit = SENSORS[key][1]
    if isinstance(value, float):
        return f"{value:.2f} {unit}".strip()
    return f"{value} {unit}".strip()
class SensorPalette(QListWidget):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for key, (label, _) in SENSORS.items():
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.addItem(item)
    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(item.data(Qt.ItemDataRole.UserRole))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
class SensorCard(QFrame):
    def __init__(self, key, on_remove):
        super().__init__()
        self.key = key
        self.setObjectName("sensorCard")
        self.setMinimumWidth(180)
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        name = QLabel(SENSORS[key][0])
        name.setObjectName("cardTitle")
        name.setWordWrap(True)
        name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        remove = QPushButton("×")
        remove.setObjectName("removeButton")
        remove.setFixedSize(26, 26)
        remove.clicked.connect(lambda: on_remove(key))
        header.addWidget(name, 1)
        header.addWidget(remove)
        layout.addLayout(header)
        self.title = name
        self.value = QLabel("--")
        self.value.setObjectName("sensorValue")
        self.value.setWordWrap(True)
        self.value.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.value, 1)
        QTimer.singleShot(0, self.fit_fonts)
    def fit_label(self, label, min_size, max_size):
        text = label.text()
        width = label.contentsRect().width() - 8
        height = label.contentsRect().height() - 8
        if width <= 8 or height <= 8:
            return
        best = min_size
        for size in range(min_size, max_size + 1):
            font = label.font()
            font.setPixelSize(size)
            metrics = QFontMetrics(font)
            bounds = metrics.boundingRect(QRect(0, 0, width, 10000), int(Qt.TextFlag.TextWordWrap), text)
            if bounds.width() <= width and bounds.height() <= height:
                best = size
            else:
                break
        font = label.font()
        if font.pixelSize() != best:
            font.setPixelSize(best)
            label.setFont(font)
    def fit_fonts(self):
        self.fit_label(self.title, 11, 38)
        self.fit_label(self.value, 12, 96)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.fit_fonts)
    def update_value(self, value):
        text = display_value(self.key, value)
        if text != self.value.text():
            self.value.setText(text)
            QTimer.singleShot(0, self.fit_fonts)
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.cards = {}
        self.values = {}
        self.grid = QGridLayout(self)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for key in ("battery_voltage", "line_current", "gear", "direction", "motor_temperature", "warnings"):
            self.add_sensor(key)
    def add_sensor(self, key):
        if key not in SENSORS or key in self.cards:
            return
        card = SensorCard(key, self.remove_sensor)
        self.cards[key] = card
        card.update_value(self.values.get(key))
        self.rearrange()
    def remove_sensor(self, key):
        card = self.cards.pop(key, None)
        if card is not None:
            self.grid.removeWidget(card)
            card.deleteLater()
            self.rearrange()
    def rearrange(self):
        width = max(1, self.width() - 24)
        columns = max(1, min(4, width // 250))
        card_width = max(180, (width - (columns - 1) * self.grid.spacing()) // columns)
        card_height = max(135, min(350, int(card_width * 0.58)))
        for card in self.cards.values():
            self.grid.removeWidget(card)
        for column in range(4):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for i, card in enumerate(self.cards.values()):
            card.setFixedHeight(card_height)
            self.grid.addWidget(card, i // columns, i % columns)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rearrange()
    def refresh(self, values):
        self.values.update(values)
        for key, card in self.cards.items():
            card.update_value(self.values.get(key))
    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() in SENSORS:
            event.acceptProposedAction()
    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() in SENSORS:
            event.acceptProposedAction()
    def dropEvent(self, event):
        if event.mimeData().hasText():
            key = event.mimeData().text()
            if key in SENSORS:
                self.add_sensor(key)
                event.acceptProposedAction()
class Panel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fardriver Sensor Dashboard")
        self.resize(1050, 710)
        self.ble = None
        self.fd = None
        self.running = True
        self.task = None
        outer = QVBoxLayout(self)
        self.connection = QLabel("Starting Bluetooth scan...")
        self.connection.setObjectName("connectionStatus")
        self.connection.setFixedHeight(28)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("Available sensors (drag to dashboard)"))
        self.palette = SensorPalette()
        sidebar_layout.addWidget(self.palette)
        splitter.addWidget(sidebar)
        self.dashboard = Dashboard()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.dashboard)
        splitter.addWidget(scroll)
        splitter.setSizes([270, 780])
        outer.addWidget(splitter, 1)
        self.debug = QPlainTextEdit()
        self.debug.setReadOnly(True)
        self.debug.setFixedHeight(64)
        self.debug.setPlaceholderText("BLE and parser messages")
        outer.addWidget(self.connection)
        outer.addWidget(self.debug)
        self.setStyleSheet("""
            QWidget { background: #151922; color: #edf1f7; font-size: 14px; }
            QListWidget { background: #202633; border: 1px solid #354155; border-radius: 7px; padding: 5px; }
            QListWidget::item { padding: 9px; }
            QListWidget::item:selected { background: #35577b; }
            QFrame#sensorCard { background: #252d3b; border: 1px solid #39485d; border-radius: 10px; }
            QLabel#cardTitle { color: #bac8dc; }
            QLabel#sensorValue { color: #ffffff; font-weight: 600; }
            QPushButton#removeButton { background: #394254; color: #fff; border: none; border-radius: 13px; font-size: 18px; }
            QPushButton#removeButton:hover { background: #a84343; }
            QLabel#connectionStatus { padding: 4px; font-size: 12px; }
            QPlainTextEdit { background: #10141c; border: 1px solid #354155; border-radius: 5px; padding: 4px; font-size: 11px; }
        """)
    def refresh(self):
        if self.fd is None:
            return
        values = {}
        for key in self.dashboard.cards:
            method = getattr(self.fd, key, None)
            if callable(method):
                try:
                    values[key] = method()
                except Exception as exc:
                    values[key] = None
                    self.debug.appendPlainText(f"{key}: {exc}")
        self.dashboard.refresh(values)
    def set_status(self, message):
        self.connection.setText(message)
        self.debug.appendPlainText(message)
    async def monitor(self):
        while self.running:
            try:
                self.set_status(f"Searching for {DEVICE_NAME}...")
                device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout = 10.0)
                if device is None:
                    raise ConnectionError(f"{DEVICE_NAME} not found")
                self.set_status(f"Connecting to {device.address}...")
                self.ble = Bledev(device, UUID, UUID)
                self.fd = Fd(self.ble)
                await self.ble.connect()
                self.set_status(f"Connected: {device.name} ({device.address})")
                while self.running and self.ble.client.is_connected:
                    try:
                        count = await self.fd.update(timeout = 5.0)
                        if count:
                            self.refresh()
                    except asyncio.TimeoutError:
                        self.set_status("Connected, but no notifications received recently")
                if self.running:
                    raise ConnectionError("Bluetooth disconnected")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.set_status(f"Disconnected: {exc} | Retrying...")
                if self.running:
                    await asyncio.sleep(3)
            finally:
                if self.ble is not None:
                    try:
                        await self.ble.disconnect()
                    except Exception:
                        pass
                self.ble = None
                self.fd = None
    def closeEvent(self, event):
        self.running = False
        event.accept()
app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)
panel = Panel()
panel.show()
with loop:
    panel.task = loop.create_task(panel.monitor())
    app.aboutToQuit.connect(loop.stop)
    loop.run_forever()
    panel.task.cancel()
    loop.run_until_complete(asyncio.gather(panel.task, return_exceptions = True))
