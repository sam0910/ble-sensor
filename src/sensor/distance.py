from machine import Pin, time_pulse_us
from time import sleep_us, sleep_ms


class HCSR04:
    def __init__(self, trigger_pin=26, echo_pin=25):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.value(0)  # Initialize trigger pin to LOW

    def measure_distance_cm(self):
        # Trigger pulse
        self.trigger.value(0)
        sleep_us(5)
        self.trigger.value(1)
        sleep_us(10)
        self.trigger.value(0)

        # Measure echo pulse duration
        duration = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout

        # Return -1 if timeout occurs
        if duration < 0:
            return 0

        # Calculate distance in cm
        # Speed of sound is approximately 343m/s or 34300cm/s
        # Distance = (duration / 2) * speed of sound
        # Division by 2 because sound travels to object and back
        distance = (duration * 34300) // 2000000

        return distance

    def continuous_measurement(self):
        while True:
            distance = self.measure_distance_cm()
            print("Distance:", distance, "cm")
            sleep_ms(500)  # 500ms interval


# Usage example:
if __name__ == "__main__":
    sensor = HCSR04(trigger_pin=26, echo_pin=25)
    sensor.continuous_measurement()
