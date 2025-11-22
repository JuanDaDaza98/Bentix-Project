# network_sender.py -> RPI REMOTE
import socket
from time import sleep
import time
import threading
import json

class DroneSender:
    def __init__(self, ip="192.168.4.3", control_port=5000, video_port=5001, telemetry_port=5002):
        self.ip = ip
        self.control_port = control_port
        self.video_port = video_port
        self.telemetry_port = telemetry_port

        self.control_socket = None
        self.video_socket = None

        # Datos de telemetría recibidos
        self.telemetry = {
            "voltage": 0.0,
            "current": 0.0,
            "battery_percent": 0
        }

        # Crear hilo TCP receptor de telemetría
        threading.Thread(target=self._listen_telemetry_tcp, daemon=True).start()

        # Conexiones TCP normales
        self._setup_control_connection()
        self._setup_video_connection()

    # ============================================================
    #  TELEMETRÍA TCP RECEIVER  (escucha al dron)
    # ============================================================
    def _listen_telemetry_tcp(self):
        print(f"🔌 Esperando telemetría DRON en TCP puerto {self.telemetry_port}...")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.telemetry_port))
        server.listen(1)

        while True:
            client, addr = server.accept()
            print(f"📡 Telemetría conectada desde {addr}")

            try:
                while True:
                    data = client.recv(128)
                    if not data:
                        break

                    voltage, current, soc = data.decode().split(",")

                    self.telemetry["voltage"] = float(voltage)
                    self.telemetry["current"] = float(current)
                    self.telemetry["battery_percent"] = float(soc)

            except Exception as e:
                print(f"[TEL ERROR] {e}")

            print("🔌 Telemetría desconectada, esperando reconexión...")

    # ============================================================
    #   CONTROL (TCP)
    # ============================================================
    def _setup_control_connection(self):
        if self.control_socket:
            try: self.control_socket.close()
            except: pass

        while True:
            try:
                print("📡 Intentando conectar al dron (controles)...")
                self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.control_socket.settimeout(3.0)
                self.control_socket.connect((self.ip, self.control_port))
                self.control_socket.settimeout(None)
                print("✅ Conectado al dron (controles).")
                break
            except socket.error as e:
                print(f"⏳ Esperando conexión de controles... ({e})")
                time.sleep(2)

    # ============================================================
    #   VIDEO (TCP)
    # ============================================================
    def _setup_video_connection(self):
        if self.video_socket:
            try: self.video_socket.close()
            except: pass

        while True:
            try:
                print("📺 Intentando conectar al dron (video)...")
                self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.video_socket.settimeout(3.0)
                self.video_socket.connect((self.ip, self.video_port))
                self.video_socket.settimeout(None)
                print("✅ Conectado al dron (video).")
                break
            except socket.error as e:
                print(f"⏳ Esperando conexión de video... ({e})")
                time.sleep(2)

    # ============================================================
    #   ENVIAR CONTROLES
    # ============================================================
    def send_control(self, data_list):
        try:
            message = ",".join(map(str, data_list))
            self.control_socket.sendall(message.encode())

            self.control_socket.settimeout(2.0)
            ack = self.control_socket.recv(16)
            if b"ACK" not in ack:
                raise ConnectionResetError("No se recibió ACK")
            self.control_socket.settimeout(None)

        except Exception as e:
            print(f"❌ Conexión perdida en controles. Reintentando... ({e})")
            try: self.control_socket.close()
            except: pass
            self._setup_control_connection()
            raise e

    # ============================================================
    #   OBTENER SOCKET DE VIDEO
    # ============================================================
    def get_video_socket(self):
        return self.video_socket
