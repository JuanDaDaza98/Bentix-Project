# video_receiver.py
import struct
import numpy as np
import cv2
import os


# ============================================================
#  RECEPCIÓN DE VIDEO + OCULTAR CURSOR
# ============================================================

# Ocultar cursor del mouse (solo Raspberry, requiere: sudo apt install unclutter)
os.system("unclutter -idle 0 &")


# ============================================================
#  ICONO DE LETRA EN CÍRCULO (R o D)
# ============================================================

def draw_letter_icon(frame, x, y, letter):
    """
    Dibuja un icono circular con una letra dentro (R = Remote, D = Drone)
    """
    radius = 12
    center = (x + radius, y + radius)

    # Círculo blanco
    cv2.circle(frame, center, radius, (255, 255, 255), 2)

    # Letra centrada
    cv2.putText(
        frame,
        letter,
        (x + 4, y + 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )


# ============================================================
#  ICONO DE BATERÍA
# ============================================================

def draw_battery_icon(frame, x, y, soc):
    """
    Dibuja un icono de batería en la posición (x, y)
    soc = porcentaje (0 a 100)
    """

    width = 60
    height = 25
    tip_width = 6

    # Color según porcentaje
    if soc > 50:
        color = (0, 255, 0)
    elif soc > 20:
        color = (0, 255, 255)
    else:
        color = (0, 0, 255)

    # Marco
    cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 2)

    # Punta
    cv2.rectangle(
        frame,
        (x + width, y + int(height * 0.30)),
        (x + width + tip_width, y + int(height * 0.70)),
        (255, 255, 255),
        -1
    )

    # Relleno (nivel de carga)
    fill_width = int((soc / 100.0) * (width - 4))
    cv2.rectangle(
        frame,
        (x + 2, y + 2),
        (x + 2 + fill_width, y + height - 2),
        color,
        -1
    )

    # Texto del porcentaje
    cv2.putText(
        frame,
        f"{int(soc)}%",
        (x, y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2
    )


# ============================================================
#  RECEPCIÓN DE VIDEO + HUD
# ============================================================

def receive_video_stream(video_socket_getter, remote_batt_getter, drone_telemetry_getter):

    print("🎥 Receptor de video iniciado...")

    cv2.namedWindow("Video del Dron", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Video del Dron", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    data = b""
    payload_size = struct.calcsize("<L")

    while True:
        try:
            video_socket = video_socket_getter()
            if video_socket is None:
                continue

            # Leer header (tamaño del frame)
            while len(data) < payload_size:
                packet = video_socket.recv(4096)
                if not packet:
                    raise ConnectionError("Conexión perdida.")
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("<L", packed_msg_size)[0]

            # Leer frame JPEG
            while len(data) < msg_size:
                packet = video_socket.recv(4096)
                if not packet:
                    raise ConnectionError("Conexión perdida.")
                data += packet

            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Decodificar frame
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            frame = cv2.resize(frame, (800, 480))

            # ======================================================
            # 1️⃣ BATERÍA DEL CONTROL (INA LOCAL)
            # ======================================================
            remote_bat = remote_batt_getter()

            if remote_bat["ok"]:
                draw_letter_icon(frame, 10, 35, "R")          # icono remoto
                draw_battery_icon(frame, 40, 35, remote_bat["soc"])

                cv2.putText(
                    frame,
                    f"{remote_bat['current']:.2f} A",
                    (40, 35 + 25 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )

            # ======================================================
            # 2️⃣ BATERÍA + AMPERAJE DEL DRON (TELEMETRÍA REMOTA)
            # ======================================================
            drone = drone_telemetry_getter()

            drone_soc = drone.get("battery_percent", 0)
            drone_amp = drone.get("current", 0.0)

            # Posición derecha de la pantalla
            dx = 800 - 40 - 60 - 30   # margen derecha
            dy = 35

            draw_letter_icon(frame, dx, dy, "D")
            draw_battery_icon(frame, dx + 30, dy, drone_soc)

            cv2.putText(
                frame,
                f"{drone_amp:.2f} A",
                (dx + 30, dy + 25 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

            cv2.imshow("Video del Dron", frame)

            if cv2.waitKey(1) == ord('q'):
                return

        except Exception as e:
            print(f"⚠️ Error de video: {e}")
            data = b""
            continue
