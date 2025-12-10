# main.py -> REMOTE RPI
from time import sleep
from threading import Thread
from joystick_reader import JoystickReader
from network_sender import DroneSender
from video_receiver import receive_video_stream
from battery_monitor import battery_monitor_loop, battery_data

joystick = JoystickReader()
sender = DroneSender()

connected = True


def get_drone_telemetry():
    """Obtiene la telemetría real recibida del dron."""
    return sender.get_telemetry()


def control_loop():
    global connected
    try:
        while True:
            y1, x2, y2, b1, b2 = joystick.read()
            data = [y1, x2, y2, b1, b2]

            try:
                sender.send_control(data)
                connected = True
            except:
                connected = False

            sleep(0.1)
    except KeyboardInterrupt:
        print("Finalizando controlador...")


def get_battery_data():
    return battery_data


if __name__ == "__main__":
    # Hilo del INA260 local
    t_battery = Thread(target=battery_monitor_loop, daemon=True)
    t_battery.start()

    # Hilo de control
    t_control = Thread(target=control_loop)
    t_control.start()

    # Esperar socket de video con timeout
    timeout_counter = 0
    max_timeout = 60  # 30 segundos (60 * 0.5s)
    while sender.get_video_socket() is None:
        print("Esperando conexión de video...")
        sleep(0.5)
        timeout_counter += 1
        if timeout_counter >= max_timeout:
            print("Timeout: Video no conectado, pero continuando...")
            break

    # Hilo de video con telemetría del dron
    t_video = Thread(
        target=receive_video_stream,
        args=(sender.get_video_socket, get_battery_data, get_drone_telemetry)
    )
    t_video.start()

    t_control.join()
    t_video.join()
