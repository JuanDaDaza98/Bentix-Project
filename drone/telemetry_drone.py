# telemetry_drone.py
import time
import board
import busio
from adafruit_ina260 import INA260
from network import TelemetrySender

# -------------------------
# CONFIGURACIÓN BATERÍA
# -------------------------
NUM_CELLS = 4
V_MIN = 3.5     # 0%
V_MAX = 4.2     # 100%

class DroneTelemetry:
    def __init__(self, telemetry_host="192.168.4.2", telemetry_port=5002):
        # Inicializar I2C + INA260
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ina = INA260(i2c)

        # Enviar datos al control
        self.sender = TelemetrySender(
            host=telemetry_host,
            port=telemetry_port
        )

    def read_voltage(self):
        """Voltaje total estimado (INA260 mide corriente + Vbus)."""
        return self.ina.voltage

    def read_current(self):
        """Amperios instantáneos hacia los motores."""
        return self.ina.current

    def calc_soc(self, voltage):
        """Porcentaje de batería basado en voltaje total."""
        cell_v = voltage / NUM_CELLS
        soc = (cell_v - V_MIN) / (V_MAX - V_MIN)
        return max(0, min(100, soc * 100))

    def send(self):
        """Lee INA y envía los datos al controlador."""
        voltage = self.read_voltage()
        current = self.read_current()
        soc = self.calc_soc(voltage)

        self.sender.send(voltage, current, soc)

        return voltage, current, soc
