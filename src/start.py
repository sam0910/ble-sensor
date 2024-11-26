import bluetooth
import random
import struct
import time
import json
import binascii
from aioble.ble_advertising import advertising_payload
from machine import Pin, time_pulse_us, lightsleep, freq
from sensor.distance import HCSR04
from micropython import const
import config as c
import uasyncio as asyncio
from driver.iqsbuttons import IQSButtons
import gc

DEVICE_NAME = const("NARMI000")
BTN_DOWN = const(35)
BTN_UP = const(34)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_PASSKEY_ACTION = const(31)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)
_FLAG_READ_ENCRYPTED = const(0x0200)

# org.bluetooth.service.environmental_sensing
_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
# org.bluetooth.characteristic.temperature
_TEMP_CHAR = (
    bluetooth.UUID(0x2A6E),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE | _FLAG_READ_ENCRYPTED,
)
# Custom UUID for distance
_DISTANCE_CHAR_UUID = bluetooth.UUID(0x2A5B)
_DISTANCE_CHAR = (
    _DISTANCE_CHAR_UUID,
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE | _FLAG_READ_ENCRYPTED,
)
# Custom UUID for interval - using Time Interval characteristic
_INTERVAL_CHAR_UUID = bluetooth.UUID(0x2A24)
_INTERVAL_CHAR = (
    _INTERVAL_CHAR_UUID,
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE | _FLAG_READ_ENCRYPTED,
)
_ENV_SENSE_SERVICE = (
    _ENV_SENSE_UUID,
    (
        _TEMP_CHAR,
        _DISTANCE_CHAR,
        _INTERVAL_CHAR,
    ),
)
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)
_IO_CAPABILITY_DISPLAY_ONLY = const(0)
_IO_CAPABILITY_DISPLAY_YESNO = const(1)
_IO_CAPABILITY_KEYBOARD_ONLY = const(2)
_IO_CAPABILITY_NO_INPUT_OUTPUT = const(3)
_IO_CAPABILITY_KEYBOARD_DISPLAY = const(4)
_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISP = const(3)
_PASSKEY_ACTION_NUMCMP = const(4)
_ADDR_MODE = 0x00
# 0x00 - PUBLIC - Use the controller’s public address.
# 0x01 - RANDOM - Use a generated static address.
# 0x02 - RPA - Use resolvable private addresses.
# 0x03 - NRPA - Use non-resolvable private addresses.

freq(160_000_000)
gc.collect()
gc.enable()

3


class BLETemperature:
    def __init__(self, ble, name=DEVICE_NAME):
        self._ble = ble
        self.loop = asyncio.get_event_loop()
        # self.btns = IQSButtons(self.btn_cb, 35, 34, loop=self.loop)
        self._name = name
        self.t = 25
        self._load_secrets()
        self._ble.irq(self._irq)
        self._ble.config(bond=True)
        self._ble.config(le_secure=True)
        self._ble.config(mitm=True)
        self._ble.config(io=_IO_CAPABILITY_NO_INPUT_OUTPUT)
        self._ble.active(True)
        self._ble.config(addr_mode=_ADDR_MODE)
        self.distance = HCSR04()
        self.INTERVAL_MS = 1000
        self.INTERVAL_GAP = 0
        self.pending_sleep = 0
        ((self._temp_handle, self._distance_handle, self._interval_handle),) = self._ble.gatts_register_services(
            (_ENV_SENSE_SERVICE,)
        )

        self._connections = set()
        self._payload = advertising_payload(
            name=name, services=[_ENV_SENSE_UUID], appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER
        )
        self._pending_indications = {}  # Track pending indications
        print("BLE Device initialized and ready to advertise")
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("\nConnected to central device")
            self._connections.add(conn_handle)
            # Send initial interval value when device connects
            self.set_interval(self.INTERVAL_MS, indicate=True)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("\nDisconnected from central device")
            self._connections.remove(conn_handle)
            self._save_secrets()
            print("Starting advertising again...")
            self._advertise()
        elif event == _IRQ_ENCRYPTION_UPDATE:
            conn_handle, encrypted, authenticated, bonded, key_size = data
            print("encryption update", conn_handle, encrypted, authenticated, bonded, key_size)
        elif event == _IRQ_PASSKEY_ACTION:
            conn_handle, action, passkey = data
            print("passkey action", conn_handle, action, passkey)
            if action == _PASSKEY_ACTION_NUMCMP:
                accept = 1  # int(input("accept? "))
                self._ble.gap_passkey(conn_handle, action, accept)
            elif action == _PASSKEY_ACTION_DISP:
                print("displaying 1234")
                self._ble.gap_passkey(conn_handle, action, 1234)
            elif action == _PASSKEY_ACTION_INPUT:
                print("prompting for passkey")
                # passkey = int(input("passkey? "))
                self._ble.gap_passkey(conn_handle, action, passkey)
            else:
                print("unknown action")
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data
            if status == 0:
                if self.pending_sleep == 0:
                    self.pending_sleep = time.ticks_ms()
                print(f" -> Indication confirmed (handle: {conn_handle})", self.pending_sleep)

            else:
                print(f"Indication failed (handle: {conn_handle}, status: {status})")
            if conn_handle in self._pending_indications:
                del self._pending_indications[conn_handle]
        elif event == _IRQ_SET_SECRET:
            sec_type, key, value = data
            key = sec_type, bytes(key)
            value = bytes(value) if value else None
            print("set secret:", key, value)
            if value is None:
                if key in self._secrets:
                    del self._secrets[key]
                    return True
                else:
                    return False
            else:
                self._secrets[key] = value
            return True
        elif event == _IRQ_GET_SECRET:
            sec_type, index, key = data
            print("get secret:", sec_type, index, bytes(key) if key else None)
            if key is None:
                i = 0
                for (t, _key), value in self._secrets.items():
                    if t == sec_type:
                        if i == index:
                            return value
                        i += 1
                return None
            else:
                key = sec_type, bytes(key)
                return self._secrets.get(key, None)

    def btn_cb(self, args):
        btn = args[0]
        type = args[1]
        print("     [BTN_CB],", btn, type)
        if btn == 2 and type == 1:
            self.INTERVAL_MS = self.INTERVAL_MS + 1000
            print("     [INTERVAL_MS],", self.INTERVAL_MS)
            self.set_interval(self.INTERVAL_MS, indicate=True)
        elif btn == 1 and type == 1 and self.INTERVAL_MS > 1000:
            self.INTERVAL_MS = self.INTERVAL_MS - 1000
            print("     [INTERVAL_MS],", self.INTERVAL_MS)
            self.set_interval(self.INTERVAL_MS, indicate=True)

    def set_temperature(self, temp_deg_c, notify=False, indicate=False):
        # Write the local value, ready for a central to read.
        self._ble.gatts_write(self._temp_handle, struct.pack("<h", int(temp_deg_c * 100)))
        if notify or indicate:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(conn_handle, self._temp_handle)
                    print("- Sending TEMPERATURE notify")
                if indicate:
                    self._pending_indications[conn_handle] = time.ticks_ms()
                    self._ble.gatts_indicate(conn_handle, self._temp_handle)
                    print(f"- Sending TEMPERATURE indication (handle: {conn_handle})")

    def measure_distance(self):
        return self.distance.measure_distance_cm()

    def set_distance(self, distance_cm, notify=False, indicate=False):
        # Pack distance as uint16 in mm
        self._ble.gatts_write(self._distance_handle, struct.pack("<H", int(distance_cm * 10)))
        if notify or indicate:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(conn_handle, self._distance_handle)
                if indicate:
                    self._pending_indications[conn_handle] = time.ticks_ms()
                    self._ble.gatts_indicate(conn_handle, self._distance_handle)
                    print(f"- Sending DISTANCE indication (handle: {conn_handle})")

    # Add new method to set interval
    def set_interval(self, interval_ms, notify=False, indicate=False):
        self._ble.gatts_write(self._interval_handle, struct.pack("<I", interval_ms))
        if notify or indicate:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(conn_handle, self._interval_handle)
                if indicate:
                    self._pending_indications[conn_handle] = time.ticks_ms()
                    self._ble.gatts_indicate(conn_handle, self._interval_handle)
                    print(f"- Sending INTERVAL indication (handle: {conn_handle})")

    def _advertise(self, interval_us=200000):
        mac = self._ble.config("mac")
        mac_address_str = ":".join([f"{b:02x}" for b in mac[1]])
        print("\nStarting BLE advertising with address:", mac_address_str)
        self._payload = advertising_payload(
            name=self._name, services=[_ENV_SENSE_UUID], appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER
        )
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def _reset_secrets(self):
        self._secrets = []
        self._save_secrets()

    def _load_secrets(self):
        self._secrets = {}
        try:
            with open("secrets.json", "r") as f:
                entries = json.load(f)
                for sec_type, key, value in entries:
                    self._secrets[sec_type, binascii.a2b_base64(key)] = binascii.a2b_base64(value)
        except:
            print("no secrets available")

    def _save_secrets(self):
        try:
            with open("secrets.json", "w") as f:
                json_secrets = [
                    (sec_type, binascii.b2a_base64(key), binascii.b2a_base64(value))
                    for (sec_type, key), value in self._secrets.items()
                ]
                json.dump(json_secrets, f)
        except:
            print("failed to save secrets")

    async def update_temperature(self):
        while True:
            self.set_temperature(self.t, notify=False, indicate=True)
            self.t += random.uniform(-0.5, 0.5)
            distance = self.measure_distance()
            self.set_distance(distance, notify=False, indicate=True)
            await asyncio.sleep_ms(self.INTERVAL_MS)
            await asyncio.sleep_ms(self.INTERVAL_GAP)

    async def update_distance(self):
        while True:
            pass

    async def loops(self):
        self.loop.run_forever()

    async def check_buttons(self):
        while True:
            await asyncio.sleep_ms(500)
            print("Checking buttons", Pin(BTN_DOWN).value(), Pin(BTN_UP).value())

    async def go_sleep(self):
        while True:
            await asyncio.sleep_ms(500)
            if self.pending_sleep > 0:
                print("pending_sleep > 0", self.pending_sleep)
                after_pending_sleep = time.ticks_diff(time.ticks_ms(), self.pending_sleep)
                print(
                    f"after_pending_sleep({after_pending_sleep}) = time.ticks_diff(time.ticks_ms({time.ticks_ms()}), self.pending_sleep({self.pending_sleep}))"
                )
                print("after_pending_sleep", after_pending_sleep, ",sleeps for", self.INTERVAL_MS)
                if after_pending_sleep > 3000:
                    print("Going to sleep")
                    await asyncio.sleep_ms(100)

                    lightsleep(self.INTERVAL_MS)
                    self.pending_sleep = 0

    def start(self):
        self.btns = IQSButtons(self.btn_cb, 35, 34, loop=self.loop)
        temp_task = self.loop.create_task(self.update_temperature())
        # temp_task = self.loop.create_task(self.check_buttons())
        # ps = self.loop.create_task(self.go_sleep())

        try:
            asyncio.run(self.loops())

        except KeyboardInterrupt:
            print("Interrupted")
            temp_task.cancel()
            # dist_task.cancel()
        finally:
            self.loop.close()


if __name__ == "__main__":
    ble = bluetooth.BLE()
    temp = BLETemperature(ble)

    temp.start()
