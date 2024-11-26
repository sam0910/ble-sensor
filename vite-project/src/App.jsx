import { useState, useEffect } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import { Button } from "@/components/ui/button";
import { BLEProvider, useBLE } from "./contexts/BLEContext";
import { useInstallPrompt } from "./hooks/useInstallPrompt";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useMediaQuery } from "react-responsive";

// ipconfig getifaddr en0
function BLEControl() {
    const { isConnected, connectToDevice, disconnect, temperature, distance, interval, lastReceived } = useBLE();
    const [dataCounter, setDataCounter] = useState(0);

    useEffect(() => {
        if (temperature !== null || distance !== null || interval !== null) {
            setDataCounter((prev) => prev + 1);
        }
    }, [temperature, distance, interval]);

    useEffect(() => {
        if (!isConnected) {
            setDataCounter(0);
        }
    }, [isConnected]);

    return (
        <Card className="w-full p-2">
            <CardHeader>
                <CardTitle className="text-2xl md:text-3xl text-center">BLE Control</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
                {isConnected ? (
                    <>
                        <Button variant="destructive" size="lg" onClick={disconnect}>
                            Disconnect
                        </Button>
                        <div className="text-xl md:text-2xl">
                            <Label>
                                Temperature:
                                <Badge className="ml-2">
                                    {temperature !== null ? `${temperature.toFixed(2)}°C` : "Reading..."}
                                </Badge>
                            </Label>
                        </div>
                        <div className="text-xl md:text-2xl">
                            <Label>
                                Distance:
                                <Badge className="ml-2">
                                    {distance !== null ? `${distance.toFixed(1)} cm` : "Reading..."}
                                </Badge>
                            </Label>
                        </div>
                        <div className="text-xl md:text-2xl">
                            <Label>
                                Interval:
                                <Badge className="ml-2">{interval !== null ? `${interval} ms` : "Reading..."}</Badge>
                            </Label>
                        </div>
                        <div className="text-sm md:text-base text-center">
                            <Label>
                                Last Update:
                                <Badge variant="outline" className="ml-2">
                                    {lastReceived || "N/A"}
                                </Badge>
                            </Label>
                        </div>
                    </>
                ) : (
                    <Button size="lg" onClick={connectToDevice}>
                        Connect to Device
                    </Button>
                )}
                <div className="text-base md:text-lg text-center flex items-center justify-center gap-2">
                    <Label>
                        Status:
                        <Badge variant={isConnected ? "success" : "destructive"} className="ml-2">
                            {isConnected ? "Connected" : "Disconnected"}
                        </Badge>
                    </Label>
                    {isConnected && (
                        <Label>
                            Received:
                            <Badge variant="outline" className="ml-2">
                                {dataCounter}
                            </Badge>
                        </Label>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

function InstallButton() {
    const { isInstallable, installApp } = useInstallPrompt();

    if (!isInstallable) return null;

    return (
        <Button size="lg" onClick={installApp} className="mt-4">
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
            <div className="flex flex-col justify-center items-center bg-gray-100 rounded-2xl p-6">
                <img src={reactLogo} alt="React Logo" className="w-16 h-16 md:w-24 md:h-24 pt-4" />
                <Label className="text-4xl md:text-5xl font-bold mb-4 text-center" style={{ color: "#61DAFB" }}>
                    NARMI
                </Label>
                <InstallButton />
                <BLEControl />
            </div>
        </BLEProvider>
    );
}

export default App;
