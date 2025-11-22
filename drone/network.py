# network.py -> DRONE RPI
import socket
import threading
from time import sleep


# ============================================================
#  CONTROL RECEIVER  (recibe joystick → dron)
# ============================================================
class ControlReceiver:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.client = None
        self.running = False

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[CONTROL] Esperando conexión en {self.host}:{self.port} ...")
        self.client, addr = self.socket.accept()
        print(f"[CONTROL] Conectado desde {addr}")
        self.running = True

    def receive(self):
        try:
            data = self.client.recv(1024)
            if not data:
                raise ConnectionResetError
            self.client.send(b"ACK\n")
            return list(map(int, data.decode().split(',')))
        except (ConnectionResetError, BrokenPipeError, socket.error, ValueError):
            print("❗ Conexión de control perdida. Esperando reconexión...")
            self.start()
            return []

    def stop(self):
        self.running = False
        if self.client:
            self.client.close()
        if self.socket:
            self.socket.close()



# ============================================================
#  VIDEO RECEIVER  (envía frames → control)
# ============================================================
class VideoReceiver:
    def __init__(self, host="0.0.0.0", port=5001):
        self.host = host
        self.port = port
        self.socket = None
        self.client = None
        self.running = False

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[VIDEO] Esperando conexión en {self.host}:{self.port} ...")
        self.client, addr = self.socket.accept()
        print(f"[VIDEO] Conectado desde {addr}")
        self.running = True

    def send(self, frame_bytes: bytes):
        try:
            self.client.sendall(frame_bytes)
        except:
            print("[VIDEO] Error enviando frame")

    def stop(self):
        self.running = False
        if self.client:
            self.client.close()
        if self.socket:
            self.socket.close()



# ============================================================
#  TELEMETRY SENDER  (envía voltaje, amperios, SoC → control)
# ============================================================
class TelemetrySender:
    """
    Enviar telemetría del dron (Voltage, Current, SoC)
    hacia la Raspberry de control.
    """
    def __init__(self, host="192.168.4.2", port=5002):
        self.host = host
        self.port = port
        self.socket = None
        self._connect()

    def _connect(self):
        while True:
            try:
                print(f"[TEL] Intentando conectar telemetría a {self.host}:{self.port} ...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                print("[TEL] Telemetría conectada.")
                break
            except Exception as e:
                print(f"[TEL] Reintentando telemetría... ({e})")
                sleep(2)

    def send(self, voltage: float, current: float, soc: float):
        """
        Enviar los datos formateados como texto:
        "voltaje,current,soc"
        """
        try:
            message = f"{voltage:.2f},{current:.2f},{soc:.1f}"
            self.socket.sendall(message.encode())
        except Exception:
            print("❌ Telemetría desconectada, reconectando...")
            try:
                self.socket.close()
            except:
                pass
            self._connect()  # reconexión automática
