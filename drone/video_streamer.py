import cv2
import struct
from time import sleep
from network import VideoReceiver

video_receiver = VideoReceiver()

def video_stream(client_socket):
    print("🎥 Iniciando transmisión de video desde la cámara...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error al capturar frame.")
                break

            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            data = buffer.tobytes()
            size = len(data)

            # Envía longitud del frame (4 bytes) + datos
            client_socket.sendall(struct.pack('<L', size) + data)
            #print(f"📤 Frame enviado: {len(data)} bytes")
            
    except Exception as e:
        print(f"⚠️ Error de transmisión: {e}")
    finally:
        cap.release()
        video_receiver.stop()
        print("🔁 Transmisión de video finalizada.")
