import time
import board
import busio
from adafruit_ina260 import INA260

INA260_ADDR = 0x40
NUM_CELLS = 2
V_MIN = 3.5
V_MAX = 4.2

battery_data = {
    "voltage": 0.0,
    "current": 0.0,
    "soc": 0.0,
    "ok": False
}

def battery_percentage(voltage):
    v_cell = voltage / NUM_CELLS
    soc = (v_cell - V_MIN) / (V_MAX - V_MIN)
    return max(0, min(100, soc * 100))

def battery_monitor_loop():
    global battery_data

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        ina = INA260(i2c, address=INA260_ADDR)
        print("INA260 inicializado.")
    except Exception as e:
        print(f"Error inicializando INA260: {e}")
        while True:
            battery_data["ok"] = False
            time.sleep(1)

    while True:
        try:
            v = ina.voltage
            i = ina.current
            soc = battery_percentage(v)

            battery_data.update({
                "voltage": v,
                "current": i,
                "soc": soc,
                "ok": True
            })

        except Exception as e:
            battery_data["ok"] = False

        time.sleep(0.3)
