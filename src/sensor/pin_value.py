from machine import Pin
import time

# Setup pins as inputs
pin34 = Pin(34, Pin.IN)
pin35 = Pin(35, Pin.IN)


def read_pins():
    while True:
        # Read values from both pins
        value34 = pin34.value()
        value35 = pin35.value()

        # Print the values
        print(f"Pin 34: {value34}, Pin 35: {value35}")

        # Wait for 500ms
        time.sleep_ms(500)


if __name__ == "__main__":
    try:
        read_pins()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
