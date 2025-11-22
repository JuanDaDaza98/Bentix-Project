from gpiozero import LED
from time import sleep

class LEDController:
    def __init__(self, pins):
        """Inicializa los LEDs conectados a los pines dados"""
        pins = [17, 27, 22]
        self.leds = [LED(pin) for pin in pins]

    def turn_on(self, index=None):
        """Enciende un LED específico o todos si index es None."""
        if index is None:
            for led in self.leds:
                led.on()
        else:
            self.leds[index].on()

    def turn_off(self, index=None):
        """Apaga un LED específico o todos si index es None."""
        if index is None:
            for led in self.leds:
                led.off()
        else:
            self.leds[index].off()

    def status(self):
        """Devuelve lista con el estado actual de cada LED (True=encendido)."""
        return [led.is_lit for led in self.leds]
