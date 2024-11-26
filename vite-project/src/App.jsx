import { useState, useEffect } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import { Button } from "@/components/ui/button";
import { BLEProvider, useBLE } from "./contexts/BLEContext";
import { useInstallPrompt } from "./hooks/useInstallPrompt";
// ipconfig getifaddr en0
function BLEControl() {
    const { isConnected, connectToDevice, disconnect, temperature } = useBLE();

    return (
        <div className="flex flex-col gap-4">
            <h2 className="text-2xl font-bold">BLE Control</h2>
            {isConnected ? (
                <>
                    <Button variant="destructive" onClick={disconnect}>
                        Disconnect
                    </Button>
                    <div className="text-lg">
                        Temperature: {temperature !== null ? `${temperature.toFixed(2)}°C` : "Reading..."}
                    </div>
                </>
            ) : (
                <Button onClick={connectToDevice}>Connect to Device</Button>
            )}
            <div className="text-sm">Status: {isConnected ? "Connected" : "Disconnected"}</div>
        </div>
    );
}

function InstallButton() {
    const { isInstallable, installApp } = useInstallPrompt();

    if (!isInstallable) return null;

    return (
        <Button onClick={installApp} className="mb-4">
            Install App
        </Button>
    );
}

function App() {
    const [isWebBluetoothAvailable, setIsWebBluetoothAvailable] = useState(false);

    useEffect(() => {
        setIsWebBluetoothAvailable("bluetooth" in navigator);
    }, []);

    if (!isWebBluetoothAvailable) {
        return <div className="p-4">Web Bluetooth is not available in your browser</div>;
    }

    return (
        <BLEProvider>
            <div className="container mx-auto p-4">
                <h1 className="text-3xl font-bold mb-8">NARMI</h1>
                <InstallButton />
                <BLEControl />
            </div>
        </BLEProvider>
    );
}

export default App;
