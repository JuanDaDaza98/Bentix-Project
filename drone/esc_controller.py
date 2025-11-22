import time
from motor_controller import MotorController

# Valores típicos de los ESC
MIN_US = 1000
NEUTRAL_US = 1500
MAX_US = 2000

def us_to_all(mc, us, channels=(0,1,2,3)):
    duty = mc.us_to_duty(us)
    for ch in channels:
        mc.pca.channels[ch].duty_cycle = duty

def calibrate_all():
    print("=== CALIBRACIÓN ESC ===")
    print("1) Retira las hélices antes de continuar ⚠️")
    print("2) Conecta el cable de señal, pero NO conectes aún la batería de los ESC.")
    input("   Presiona Enter cuando estés listo...")

    # Enviar señal máxima
    print(f"→ Enviando señal MÁXIMA ({MAX_US} µs)...")
    us_to_all(mc, MAX_US)
    time.sleep(0.5)

    input("   Ahora conecta la batería de los ESC. Espera los pitidos y luego presiona Enter...")

    # Mantener señal máxima unos segundos
    time.sleep(2)

    # Cambiar a señal mínima
    print(f"→ Enviando señal MÍNIMA ({MIN_US} µs)...")
    us_to_all(mc, MIN_US)
    time.sleep(3)

    # Enviar neutro
    print(f"→ Enviando señal NEUTRAL ({NEUTRAL_US} µs)...")
    us_to_all(mc, NEUTRAL_US)
    time.sleep(1)

    print("✅ Calibración completada.")

if __name__ == "__main__":
    try:
        mc = MotorController()
        calibrate_all()
    except KeyboardInterrupt:
        us_to_all(mc, NEUTRAL_US)
        print("\nNeutro enviado. Saliendo con seguridad.")
