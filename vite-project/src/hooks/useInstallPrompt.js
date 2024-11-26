import { useState, useEffect } from "react";

export const useInstallPrompt = () => {
    const [prompt, setPrompt] = useState(null);
    const [isInstallable, setIsInstallable] = useState(false);

    useEffect(() => {
        const ready = (e) => {
            e.preventDefault();
            setPrompt(e);
            setIsInstallable(true);
        };

        window.addEventListener("beforeinstallprompt", ready);

        return () => {
            window.removeEventListener("beforeinstallprompt", ready);
        };
    }, []);

    const installApp = async () => {
        if (!prompt) return;

        const result = await prompt.prompt();
        if (result.outcome === "accepted") {
            setIsInstallable(false);
        }
    };

    return { isInstallable, installApp };
};
