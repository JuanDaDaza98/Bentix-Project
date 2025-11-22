import board
import busio

print("SCL:", board.SCL)
print("SDA:", board.SDA)

i2c = busio.I2C(board.SCL, board.SDA)
print("✅ I2C iniciado correctamente.")
