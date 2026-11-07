import asyncio
class Fd:
    ADDR = (
        0xE2, 0xE8, 0xEE, 0xE4, 0x06, 0x0C, 0x12,
        0xE2, 0xE8, 0xEE, 0x18, 0x1E, 0x24, 0x2A,
        0xE2, 0xE8, 0xEE, 0x30, 0x5D, 0x63, 0x69,
        0xE2, 0xE8, 0xEE, 0x7C, 0x82, 0x88, 0x8E,
        0xE2, 0xE8, 0xEE, 0x94, 0x9A, 0xA0, 0xA6,
        0xE2, 0xE8, 0xEE, 0xAC, 0xB2, 0xB8, 0xBE,
        0xE2, 0xE8, 0xEE, 0xC4, 0xCA, 0xD0,
        0xE2, 0xE8, 0xEE, 0xD6, 0xDC, 0xF4, 0xFA,
    )
    FAULT_NAMES = (
        'Motor Hall fault', 'Throttle fault', 'Current-protection restart',
        'Phase-current surge protection', 'Voltage protection',
        'Anti-theft / alarm protection', 'Motor overtemperature',
        'Controller overtemperature', 'Phase-current overflow',
        'Phase-current zero-point fault', 'Phase-line/current protection',
        'Line-current zero-point fault', 'MOSFET high-side fault',
        'MOSFET low-side fault', 'Peak current protection',
    )
    D6_FLAGS = {
        'motor_running': (3, 0),
        'hall_position_error': (1, 2),
        'phase_lost_alarm': (3, 3),
        'motor_running_secondary': (3, 5),
        'eabs_started': (4, 6),
        'low_voltage_stop': (4, 4),
        'gear_disabled': (5, 1),
        'speed_limited': (5, 3),
        'middle_speed_enabled': (5, 4),
        'high_speed_enabled': (5, 5),
        'anti_theft_enabled': (5, 6),
        'anti_theft_brake': (5, 7),
        'speed_limit_enabled': (6, 4),
        'flash_error': (8, 1),
        'encoder_ab_error': (9, 0),
        'encoder_z_error': (9, 1),
        'encoder_position_error': (9, 2),
        'encoder_magnet_error': (9, 3),
        'encoder_angle_error': (9, 6),
    }
    FA_FLAGS = {
        'error_stop': (4, 0),
        'block_state': (5, 5),
        'eabs_state': (5, 6),
        'brake_control': (5, 7),
        'gear_control': (9, 4),
        'hx_control': (9, 5),
        'tbar_control': (9, 6),
        'hbar_control': (9, 7),
    }
    PIN_NAMES = (
        'pause_park', 'side_stand', 'cruise', 'boost',
        'low_speed', 'high_speed', 'reverse', 'forward',
        'switch_voltage', 'seat', 'anti_theft', 'charge',
    )
    def __init__(self, bledev, crc_check = True):
        self.ble = bledev
        self.crc_check = crc_check
        self.buffer = bytearray()
        self.memory = {}
        self.frames = {}
        self.frame_ids = {}
        self.frame_count = 0
        self.crc_errors = 0
        self.header_errors = 0
    @staticmethod
    def verify_crc(frame):
        if len(frame) != 16 or frame[0] != 0xAA:
            return False
        crc = 0x7F3C
        for byte in frame[:14]:
            crc ^= byte
            for _ in range(8):
                crc = ((crc >> 1) ^ 0xA001) if crc & 1 else (crc >> 1)
        return (crc & 0xFFFF) == int.from_bytes(frame[14:16], 'little')
    def parse(self, data):
        if not data:
            return 0
        self.buffer.extend(data)
        count = 0
        while len(self.buffer) >= 16:
            if self.buffer[0] != 0xAA:
                del self.buffer[0]
                continue
            frame = bytes(self.buffer[:16])
            frame_id = frame[1] & 0x3F
            if frame_id >= len(self.ADDR):
                self.header_errors += 1
                del self.buffer[0]
                continue
            if self.crc_check is not False and self.crc_check is not None:
                valid = (self.crc_check(frame) if callable(self.crc_check)
                         else self.verify_crc(frame))
                if not valid:
                    self.crc_errors += 1
                    del self.buffer[0]
                    continue
            del self.buffer[:16]
            address = self.ADDR[frame_id]
            payload = frame[2:14]
            self.frames[address] = payload
            self.frame_ids[frame_id] = payload
            for i in range(6):
                self.memory[address + i] = int.from_bytes(
                    payload[2 * i:2 * i + 2], 'little'
                )
            count += 1
            self.frame_count += 1
        return count
    async def update(self, timeout = 2.0):
        data = await asyncio.wait_for(self.ble.receive(), timeout = timeout)
        return self.parse(data)
    async def listen(self, callback = None):
        while True:
            count = await self.update(timeout = None)
            if count and callback is not None:
                result = callback(self.status())
                if asyncio.iscoroutine(result):
                    await result
    def word(self, address, signed = False):
        value = self.memory.get(address)
        if value is None:
            return None
        return value - 65536 if signed and value >= 32768 else value
    def byte(self, address, byte_index = 0):
        word = self.word(address)
        return None if word is None else (word >> (8 * byte_index)) & 0xFF
    def _payload(self, address):
        return self.frames.get(address)
    def _flag(self, address, byte_index, bit):
        payload = self._payload(address)
        return None if payload is None or byte_index >= len(payload) else bool(payload[byte_index] & (1 << bit))
    def _scaled(self, address, divisor = 1, signed = False):
        value = self.word(address, signed = signed)
        return None if value is None else value / divisor
    def forward(self):
        return self._flag(0xE2, 0, 0)
    def reverse(self):
        return self._flag(0xE2, 0, 1)
    def gear_raw(self):
        payload = self._payload(0xE2)
        return None if payload is None else (payload[0] >> 2) & 3
    def gear(self):
        raw = self.gear_raw()
        return None if raw is None else raw + 1
    def moving(self):
        return self._flag(0xE2, 0, 5)
    def sliding_backwards(self):
        return self._flag(0xE2, 0, 4)
    def brake(self):
        return self._flag(0xE2, 3, 7)
    def modulation(self):
        data = self._payload(0xE2)
        return None if data is None else data[4] / 128.0
    def measured_speed_raw(self):
        return self.word(0xE5)
    def warnings(self):
        data = self._payload(0xE2)
        if data is None:
            return None
        mask = data[2] | ((data[3] & 0x7F) << 8)
        return [name for bit, name in enumerate(self.FAULT_NAMES) if mask & (1 << bit)]
    def fault_mask(self):
        data = self._payload(0xE2)
        return None if data is None else data[2] | ((data[3] & 0x7F) << 8)
    def battery_voltage(self):
        return self._scaled(0xE8, 10, signed = True)
    def line_current(self):
        return self._scaled(0xEA, 4, signed = True)
    def battery_power(self):
        voltage, current = self.battery_voltage(), self.line_current()
        return None if voltage is None or current is None else voltage * current
    def throttle_depth_raw(self):
        return self.word(0xED, signed = True)
    def motor_temperature(self):
        return self.word(0xF4, signed = True)
    def controller_temperature(self):
        return self.word(0xDB, signed = True)
    def battery_soc_raw(self):
        return self.byte(0xF5, 1)
    def controller_flags(self):
        result = {}
        for name, (byte, bit) in self.D6_FLAGS.items():
            result[name] = self._flag(0xD6, byte, bit)
        for name, (byte, bit) in self.FA_FLAGS.items():
            result[name] = self._flag(0xFA, byte, bit)
        return result
    def configured_pin_selectors(self):
        data = self._payload(0x69)
        if data is None:
            return None
        packed = data[:6]
        nibbles = [(b & 0x0F, b >> 4) for b in packed]
        values = [x for pair in nibbles for x in pair]
        return dict(zip(self.PIN_NAMES, values))
    def rated_voltage(self):
        return self._scaled(0x17, 10)
    def max_line_current(self):
        return self._scaled(0x19, 4)
    def max_phase_current(self):
        return self._scaled(0x2D, 4)
    def low_voltage_cutoff(self):
        return self._scaled(0x1F, 10)
    def high_voltage_cutoff(self):
        return self._scaled(0x25, 10)
    def pole_pairs(self):
        return self.byte(0x14)
    def rated_power(self):
        return self.word(0x16)
    def max_speed_setting(self):
        return self.word(0x15)
    def rated_speed(self):
        return self.word(0x18)
    def throttle_voltage_setting(self):
        return self._scaled(0x82, 100)
    def park_enabled_setting(self):
        return self._flag(0x1E, 6, 2)
    def reverse_enabled_setting(self):
        return self._flag(0x1E, 7, 6)
    def cruise_enabled_setting(self):
        return self._flag(0x1E, 6, 4)
    def eabs_enabled_setting(self):
        return self._flag(0x1E, 6, 5)
    def raw_frames(self):
        return self.frames.copy()
    def raw_frame_ids(self):
        return self.frame_ids.copy()
    def memory_copy(self):
        return self.memory.copy()
