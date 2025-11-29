# video_receiver.py
import struct
import numpy as np
import cv2
import os


# ------------------------------------------------------------
#  Helpers para recursos y overlays con alpha
# ------------------------------------------------------------

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'BentiX Interface Indicators'))


def load_png(name):
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path):
        return cv2.imread(path, cv2.IMREAD_UNCHANGED)  # keep alpha if present
    return None


def overlay_image_alpha(img, overlay, x, y, overlay_size=None):
    """Overlay `overlay` onto `img` at position (x, y) and blend using alpha channel.

    overlay may have alpha channel (4th). If overlay_size provided, overlay is resized first.
    """
    if overlay is None:
        return img

    ol = overlay.copy()
    if overlay_size is not None:
        ol = cv2.resize(ol, overlay_size, interpolation=cv2.INTER_AREA)

    h, w = ol.shape[0], ol.shape[1]
    if y + h > img.shape[0] or x + w > img.shape[1] or x < 0 or y < 0:
        # clip overlay region to image bounds
        w = min(w, img.shape[1] - x)
        h = min(h, img.shape[0] - y)
        if w <= 0 or h <= 0:
            return img
        ol = ol[0:h, 0:w]

    if ol.shape[2] == 4:
        alpha = ol[:, :, 3] / 255.0
        for c in range(0, 3):
            img[y:y+h, x:x+w, c] = (alpha * ol[:, :, c] + (1 - alpha) * img[y:y+h, x:x+w, c])
    else:
        img[y:y+h, x:x+w] = ol

    return img


# ============================================================
#  RECEPCIÓN DE VIDEO + OCULTAR CURSOR
# ============================================================

# Ocultar cursor del mouse (solo Raspberry, requiere: sudo apt install unclutter)
try:
    os.system("unclutter -idle 0 &")
except Exception:
    pass


# ============================================================
#  ICONO DE LETRA EN CÍRCULO (R o D)
# ============================================================

def draw_letter_icon(frame, x, y, letter):
    radius = 12
    center = (x + radius, y + radius)
    cv2.circle(frame, center, radius, (255, 255, 255), 2)
    cv2.putText(frame, letter, (x + 4, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


# ============================================================
#  ICONO DE BATERÍA
# ============================================================

def draw_battery_icon(frame, x, y, soc):
    width = 60
    height = 25
    tip_width = 6

    if soc > 50:
        color = (0, 255, 0)
    elif soc > 20:
        color = (0, 255, 255)
    else:
        color = (0, 0, 255)

    cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 2)
    cv2.rectangle(frame, (x + width, y + int(height * 0.30)), (x + width + tip_width, y + int(height * 0.70)), (255, 255, 255), -1)
    fill_width = int((soc / 100.0) * (width - 4))
    cv2.rectangle(frame, (x + 2, y + 2), (x + 2 + fill_width, y + height - 2), color, -1)
    cv2.putText(frame, f"{int(soc)}%", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


# ============================================================
#  RECEPCIÓN DE VIDEO + HUD con overlay de band superior
# ============================================================

def receive_video_stream(video_socket_getter, remote_batt_getter, drone_telemetry_getter):

    print("🎥 Receptor de video iniciado...")

    cv2.namedWindow("Video del Dron", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Video del Dron", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # precargar assets (nombres detectados en carpeta de recursos)
    top_band = load_png('Black band with 10% opacity.png')
    logo = load_png('BentiX Logo White.png') or load_png('BentiX Logo Black.png')
    rec_btn = load_png('REC button.png')
    low_batt_img = load_png('Low Battery.png')

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

            # Overlay: banda superior (si existe)
            if top_band is not None:
                # escalar banda al ancho del frame
                h_ratio = top_band.shape[0] / top_band.shape[1]
                band_h = int(frame.shape[1] * h_ratio)
                band_resized = cv2.resize(top_band, (frame.shape[1], band_h), interpolation=cv2.INTER_AREA)
                frame = overlay_image_alpha(frame, band_resized, 0, 0)

                # logo izquierda
                if logo is not None:
                    logo_h = int(band_resized.shape[0] * 0.85)
                    logo_w = int(logo.shape[1] * (logo_h / logo.shape[0]))
                    frame = overlay_image_alpha(frame, logo, 8, 6, overlay_size=(logo_w, logo_h))

                # REC derecha
                if rec_btn is not None:
                    rec_h = int(band_resized.shape[0] * 0.85)
                    rec_w = int(rec_btn.shape[1] * (rec_h / rec_btn.shape[0]))
                    frame = overlay_image_alpha(frame, rec_btn, frame.shape[1] - rec_w - 8, 6, overlay_size=(rec_w, rec_h))

            # dibujar borde naranja simulando el marco (pequeño)
            cv2.rectangle(frame, (2, 2), (frame.shape[1]-3, frame.shape[0]-3), (217,100,24), 8)

            # ======================================================
            # 1️⃣ BATERÍA DEL CONTROL (INA LOCAL)
            # ======================================================
            remote_bat = remote_batt_getter()

            if remote_bat["ok"]:
                draw_letter_icon(frame, 10, 35, "R")
                draw_battery_icon(frame, 40, 35, remote_bat["soc"])

                cv2.putText(frame, f"{remote_bat['current']:.2f} A", (40, 35 + 25 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # ======================================================
            # 2️⃣ BATERÍA + AMPERAJE DEL DRON (TELEMETRÍA REMOTA)
            # ======================================================
            drone = drone_telemetry_getter()

            drone_soc = drone.get("battery_percent", 0)
            drone_amp = drone.get("current", 0.0)

            # Posición derecha de la pantalla
            dx = 800 - 40 - 60 - 30
            dy = 35

            draw_letter_icon(frame, dx, dy, "D")
            draw_battery_icon(frame, dx + 30, dy, drone_soc)

            cv2.putText(frame, f"{drone_amp:.2f} A", (dx + 30, dy + 25 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # si el dron tiene low battery estado, mostrar imagen central pequeña
            if drone_soc <= 20 and low_batt_img is not None:
                # escalar low batt a 180x40 aprox
                lb_h = 40
                lb_w = int(low_batt_img.shape[1] * (lb_h / low_batt_img.shape[0]))
                frame = overlay_image_alpha(frame, low_batt_img, int((frame.shape[1]-lb_w)/2), 6, overlay_size=(lb_w, lb_h))

            cv2.imshow("Video del Dron", frame)

            if cv2.waitKey(1) == ord('q'):
                return

        except Exception as e:
            print(f"⚠️ Error de video: {e}")
            data = b""
            continue