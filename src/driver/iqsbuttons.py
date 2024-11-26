from machine import Pin, TouchPad
from utime import ticks_ms, ticks_diff
import uasyncio as asyncio
from primitives.pushbutton import Pushbutton

DIVE_BTN_THRES = 600


class IQSButtons:
    def __init__(self, out_cb, btn1, btn2, lock=None, loop=None):
        self.out_cb = out_cb
        self.dive = ["NORMAL", 0, 0, 0]

        btn1 = Pushbutton(Pin(btn1), suppress=True, sense=0, lock=lock, loop=loop)
        btn2 = Pushbutton(Pin(btn2), suppress=True, sense=1, lock=lock, loop=loop)
        Pushbutton.long_press_ms = 1200
        Pushbutton.debounce_ms = 10
        # Pushbutton.double_click_ms = 400

        cb = self.cb
        btn1.press_func(cb, (1, 0))
        btn1.release_func(cb, (1, 1))
        btn1.double_func(cb, (1, 2))
        btn1.long_func(cb, (1, 3))

        btn2.press_func(cb, (2, 0))
        btn2.release_func(cb, (2, 1))
        btn2.double_func(cb, (2, 2))
        btn2.long_func(cb, (2, 3))

    def cb(self, btn, type):
        # type_str = ("press", "release", "double", "long", "dive")

        if self.dive[0] == "DIVE":
            print("DIVE MODE - NO REACTION")
            self.dive[0] = "NORMAL"
            self.dive[1] = 0
            self.dive[2] = 0
            self.dive[3] = 0
            return

        if self.dive[0] == "PREDIVE":
            print("PRE DIVE MODE - CHECK")
            self.dive[3] = self.dive[3] + 1

            if type == 3:
                self.dive[btn] = ticks_ms()
                t_differs = abs(ticks_diff(self.dive[1], self.dive[2]))
                if t_differs < DIVE_BTN_THRES and t_differs > 0:
                    print("DIVE MODE")
                    self.dive[0] = "DIVE"
                    self.dive[1] = 0
                    self.dive[2] = 0
                    type = 4
                    self.out_cb((btn, type))
                    return

            if self.dive[3] >= 2:
                print("PRE DIVE MODE - RESET")
                self.dive[0] = "NORMAL"
                self.dive[1] = 0
                self.dive[2] = 0
                self.dive[3] = 0

            return

        if type == 0:
            self.dive[btn] = ticks_ms()
            t_differs = abs(ticks_diff(self.dive[1], self.dive[2]))

            if t_differs < DIVE_BTN_THRES and t_differs > 0:
                print("PRE DIVE MODE")
                self.dive[0] = "PREDIVE"
                self.dive[1] = 0
                self.dive[2] = 0
                return

        # if type != 0:
        self.out_cb((btn, type))
        # print(f"btn({btn})  {type_str[type]}")


if __name__ == "__main__":
    print("IQSButtons test")

    def _cb(args):
        type_str = ("press", "release", "double", "long", "dive")
        print(f"Main :: btn({args[0]}) {type_str[args[1]]}")

    async def coro1():
        try:
            while True:
                await asyncio.sleep_ms(2000)

        except asyncio.CancelledError:
            print(" - Task canceled [coro1] ")
            return

    async def loops():
        loop = asyncio.get_event_loop()
        loop.create_task(coro1())
        loop.run_forever()

    btns = IQSButtons(_cb, 34, 35)
    asyncio.run(loops())
