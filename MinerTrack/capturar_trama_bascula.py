import serial
import time
import sys

# Cambia 'COM3' por el puerto que Windows te asigne (COM4, COM5, etc.)
PUERTO = 'COM3' 
BAUDRATE = 9600

print(f"--- MODO DIAGNÓSTICO DE BÁSCULA ---")
print(f"Intentando conectar al puerto {PUERTO} a {BAUDRATE} baudios...")

try:
    conexion = serial.Serial(
        port=PUERTO,
        baudrate=BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=2
    )
    
    if conexion.is_open:
        print(f"¡CONECTADO CON ÉXITO A {PUERTO}!")
        print("Escuchando lo que envía la báscula por 15 segundos...\n")
        
        tiempo_fin = time.time() + 15
        tramas_recibidas = []
        
        while time.time() < tiempo_fin:
            if conexion.in_waiting > 0:
                # Leemos la línea cruda
                raw_data = conexion.readline()
                print(f"Dato Crudo (Raw): {raw_data}")
                tramas_recibidas.append(raw_data)
            time.sleep(0.1)
            
        conexion.close()
        print("\n--- FIN DE LECTURA ---")
        
        # Guardamos en un archivo de texto para analizarlo después
        if tramas_recibidas:
            with open("trama_bascula_real.txt", "w") as f:
                for trama in tramas_recibidas:
                    f.write(str(trama) + "\n")
            print("¡He guardado los datos en el archivo 'trama_bascula_real.txt'!")
            print("Mándale el contenido de ese archivo a Antigravity para ajustar el Parser.")
        else:
            print("No se recibió ningún dato. Verifica el cable o los baudios.")

except Exception as e:
    print(f"\n[ERROR] No me pude conectar: {e}")
    print("Asegúrate de que el cable USB Manhattan esté conectado y verifica en el 'Administrador de Dispositivos' qué número de COM tiene.")

input("\nPresiona Enter para salir...")
