./esptool-macos/esptool --chip esp32 --port /dev/cu.usbserial-56B60070291 erase_flash
./esptool-macos/esptool --chip esp32 --port /dev/cu.usbserial-56B60070291 --baud 460800 write_flash -z 0x1000 UM_TINYPICO-20241025-v1.24.0.bin

./esptool-macos/esptool --chip esp32 --port /dev/cu.usbserial-56B60070291 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-SPIRAM-20241025-v1.24.0.bin