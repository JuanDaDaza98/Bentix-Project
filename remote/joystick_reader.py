from gpiozero import MCP3008, Button

class JoystickReader:
    def __init__(self):
        self.y1 = MCP3008(channel=2, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=13)
        self.x2 = MCP3008(channel=0, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=13)
        self.y2 = MCP3008(channel=1, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=13)
        self.button1 = Button(4)
        self.button2 = Button(26)

    def read(self):
        
        y2_value = int(self.y1.value * 255)
        x2_value = int(255 - (self.x2.value * 255))
        y1_value = int(255 - (self.y2.value * 255))
        button1_state = int(self.button1.is_pressed)
        button2_state = int(self.button2.is_pressed)
        
        return y1_value, x2_value, y2_value, button1_state, button2_state
