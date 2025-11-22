import board
import busio
from adafruit_pca9685 import PCA9685
from time import sleep

class MotorController:
    def __init__(self, i2c_freq=50, center_offset=37):
        """
        Controlador de motores basado en PCA9685.

        Args:
            i2c_freq (int): Frecuencia de PWM.
            center_offset (int): Desplazamiento del centro real del joystick.
                                 Si el centro lógico es 128 y el real 165 → offset = 37.
        """
        self.center_offset = center_offset

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c, address=0x41)
            self.pca.frequency = i2c_freq
        except Exception as e:
            raise RuntimeError(f"Error initializing I2C or PCA9685: {e}")

        # 🚀 Enviar neutro a todos los motores al inicio
        neutral = self.us_to_duty(1500)
        for i in range(4):
            self.pca.channels[i].duty_cycle = neutral
        print("Motores inicializados en NEUTRO (1500 μs).")

    # --------------------------------------------------------------
    # CONVERSIONES
    # --------------------------------------------------------------

    def us_to_duty(self, microseconds: int) -> int:
        """Convierte microsegundos (1000–2000) a duty cycle (0–65535)."""
        return int(microseconds / 20000 * 0xFFFF)

    def adjust_center(self, value: int) -> int:
        """
        Ajusta el valor del joystick según el desplazamiento del centro.
        Ej: Si joystick envía 128 pero el centro físico es 165 → +37.
        """
        return max(0, min(255, value + self.center_offset))

    def map_joystick_value_to_us(self, value: int) -> int:
        """Mapea valor del joystick (0–255) a pulso ESC (1150–1850 µs)."""
        center = 165
        if value < center:
            return int(1150 + (value / center) * (1500 - 1150))
        else:
            return int(1500 + ((value - center) / (255 - center)) * (1850 - 1500))

    def clip(self, value: int, min_val: int = 0, max_val: int = 255) -> int:
        """Limita el valor dentro del rango 0–255."""
        return max(min_val, min(max_val, value))

    def clip_deadzone(self, value: int, deadzone: int = 10, center: int = 165) -> int:
        """Evita movimientos cerca del centro físico."""
        if abs(value - center) <= deadzone:
            return center
        return value

    # --------------------------------------------------------------
    # CONTROL DE MOTORES
    # --------------------------------------------------------------

    def set_motors(self, throttle: int, yaw: int, pitch: int) -> None:
        """
        Controla 4 motores:
        - M1 y M2: verticales (ascenso/descenso)
        - M3 y M4: horizontales (avance/retroceso y giro)
        """

        # Ajustar centro y aplicar zona muerta
        throttle = self.clip_deadzone(self.adjust_center(self.clip(throttle)))
        yaw = self.clip_deadzone(self.adjust_center(self.clip(yaw)))
        pitch = self.clip_deadzone(self.adjust_center(self.clip(pitch)))

        # Motores M1 y M2 (verticales)
        m1_us = self.map_joystick_value_to_us(throttle)
        m2_us = m1_us

        # Motores M3 y M4 (horizontales)
        base = pitch
        rotation = yaw - 165  # ahora centrado en 165, no en 128
        m3_input = self.clip(base + rotation)
        m4_input = self.clip(base - rotation)

        m3_us = self.map_joystick_value_to_us(m3_input)
        m4_us = self.map_joystick_value_to_us(m4_input)

        # Enviar señales PWM
        self.pca.channels[0].duty_cycle = self.us_to_duty(m1_us)
        self.pca.channels[2].duty_cycle = self.us_to_duty(m2_us)
        self.pca.channels[1].duty_cycle = self.us_to_duty(m3_us)
        self.pca.channels[3].duty_cycle = self.us_to_duty(m4_us)

#        print(f"throttle={throttle}, yaw={yaw}, pitch={pitch}")
#        print(f"M3={m3_input}, M4={m4_input} | yaw diff={rotation}")

    # --------------------------------------------------------------
    # PARADA SEGURA
    # --------------------------------------------------------------

    def stop(self):
        """Envía pulso neutro (1500 µs) a todos los motores."""
        neutral = self.us_to_duty(1500)
        for ch in self.pca.channels[:4]:
            ch.duty_cycle = neutral
        print("🛑 Todos los motores detenidos (1500 μs).")
