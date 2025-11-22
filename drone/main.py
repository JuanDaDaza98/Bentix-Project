# main.py -> DRONE RPI
import threading
from time import sleep
from motor_controller import MotorController
from led_controller import LEDController
from network import ControlReceiver, VideoReceiver
from video_streamer import video_stream
from telemetry_drone import DroneTelemetry   # <<--- CORRECTO


# === Configuración de motores, LEDs y telemetría ===
motors = MotorController()
leds = LEDController([17, 27, 22])
control_receiver = ControlReceiver()
video_receiver = VideoReceiver()


def control_loop():
    try:
        control_receiver.start()
        while True:
            data = control_receiver.receive()
            if not data or len(data) < 5:
                continue

            y1, x2, y2, b1, b2 = data

            motors.set_motors(throttle=y2, yaw=x2, pitch=y1)

            leds.turn_on() if b1 else leds.turn_off()

            sleep(0.05)

    except Exception as e:
        print(f"[CONTROL ERROR] {e}")

    finally:
        motors.stop()
        leds.turn_off()
        control_receiver.stop()



# === Hilo de telemetría (INA260 + envío al control) ===
def telemetry_loop():
    telemetry = DroneTelemetry()   # Inicializa INA260 + socket

    while True:
        try:
            telemetry.send()       # Lee INA y envía datos
            sleep(0.5)
        except Exception as e:
            print(f"[TELEMETRIA ERROR] {e}")
            sleep(1)



# === Hilo de video con reconexión automática ===
def video_loop():
    while True:
        try:
            video_receiver.start()
            video_stream(video_receiver.client)

        except Exception as e:
            print(f"[VIDEO ERROR] {e}")

        finally:
            print("🔁 Esperando nueva conexión de video...")
            sleep(2)



if __name__ == "__main__":
    # Hilos separados
    t_video = threading.Thread(target=video_loop)
    t_control = threading.Thread(target=control_loop)
    t_telemetry = threading.Thread(target=telemetry_loop)   # <<--- TELEMETRY OK

    t_video.start()
    t_control.start()
    t_telemetry.start()

    t_video.join()
    t_control.join()
    t_telemetry.join()
