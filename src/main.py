from start import BLETemperature
import bluetooth

ble = bluetooth.BLE()
temp = BLETemperature(ble)

temp.start()
# v1.2
