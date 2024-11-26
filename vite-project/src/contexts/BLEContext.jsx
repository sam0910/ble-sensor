import { createContext, useState, useContext } from "react";

const BLEContext = createContext(null);

// ESP32 Environmental Sensing Service UUID
const ENV_SENSE_UUID = 0x181a;
const TEMP_CHAR_UUID = 0x2a6e;

export const BLEProvider = ({ children }) => {
    const [device, setDevice] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [temperature, setTemperature] = useState(null);

    const connectToDevice = async () => {
        try {
            console.log("Requesting Bluetooth Device...");
            const device = await navigator.bluetooth.requestDevice({
                acceptAllDevices: true,
                optionalServices: [ENV_SENSE_UUID],
            });

            console.log("Connecting to GATT Server...");
            const server = await device.gatt.connect();

            // Request pairing if device is not bonded
            if (!device.gatt.connected) {
                console.log("Initiating pairing...");
                await device.gatt.device.watchAdvertisements();
            }

            // Add security event listeners
            device.addEventListener("advertisementreceived", (event) => {
                console.log("Advertisement received:", event);
            });

            device.addEventListener("characteristicvaluechanged", (event) => {
                // This will trigger for encrypted characteristics
                console.log("Secure characteristic value changed");
            });

            console.log("Getting Environmental Service...");
            const service = await server.getPrimaryService(ENV_SENSE_UUID);

            // Handle encrypted characteristic
            console.log("Getting Temperature Characteristic...");
            const characteristic = await service.getCharacteristic(TEMP_CHAR_UUID);

            // Enable notifications with encryption
            await characteristic.startNotifications();
            characteristic.addEventListener("characteristicvaluechanged", (event) => {
                const value = event.target.value;
                const temp = value.getInt16(0, true) / 100;
                console.log("Received encrypted temperature:", temp);
                setTemperature(temp);
            });

            setDevice(device);
            setIsConnected(true);

            // Handle disconnection
            device.addEventListener("gattserverdisconnected", () => {
                console.log("Disconnected - Bond status may need refresh");
                setIsConnected(false);
                setTemperature(null);
            });
        } catch (error) {
            console.error("Connection error:", error);
            if (error.message.includes("security")) {
                console.log("Security error - may need to forget device and repair");
            }
        }
    };

    const disconnect = () => {
        if (device) {
            device.gatt.disconnect();
            setDevice(null);
            setIsConnected(false);
        }
    };

    return (
        <BLEContext.Provider
            value={{
                device,
                isConnected,
                temperature,
                connectToDevice,
                disconnect,
            }}>
            {children}
        </BLEContext.Provider>
    );
};

export const useBLE = () => useContext(BLEContext);
