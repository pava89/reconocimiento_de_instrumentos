"""
ETAPA 2 — Captura de audio con el ESP32 (micrófonos MAX9814 y MAX4466)
-----------------------------------------------------------------------
Hace lo mismo que grabar_audio.py, pero con el hardware de la Etapa 2.
El ESP32 (programa esp32/captura_audio) mide el voltaje del micrófono
elegido y manda las muestras por el cable USB. Este script las recibe,
las convierte en una señal de audio y las guarda como .wav. Desde ahí,
el resto del proyecto (FFT, características, clasificador) funciona
igual que en la Etapa 1.

Especificaciones del muestreo (las fija el programa del ESP32):
  FS = 16000 Hz (Nyquist 8000 Hz), 2 s por grabación = 32000 muestras,
  ADC de 12 bits (0 a 4095), envío binario a 921600 baudios.

Antes de usarlo: cierra el Monitor Serie y el Serial Plotter del
Arduino IDE, porque ocupan el puerto.

Uso (desde la carpeta raíz del proyecto):
    python codigo\\grabar_esp32.py --micro max9814 referencias_max9814\\piano_1.wav
    python codigo\\grabar_esp32.py --micro max4466 referencias_max4466\\piano_1.wav
    python codigo\\grabar_esp32.py --micro max4466 prueba.wav --puerto COM5
    python codigo\\grabar_esp32.py --listar
"""

import argparse
import os
import sys
import time

import numpy as np
import serial
import soundfile as sf
from serial.tools import list_ports

BAUDIOS = 921600      # igual que BAUDIOS en esp32/captura_audio/captura_audio.ino
FS_OBJETIVO = 16000   # igual que FS en el programa del ESP32
MAX_ADC = 4095        # ADC de 12 bits: valores de 0 a 4095
VREF_APROX = 3.3      # solo para mostrar en pantalla un voltaje aproximado

# Micrófono -> letra que se le manda al ESP32 para que grabe con él
MICROFONOS = {
    "max9814": b"A",   # pin D4
    "max4466": b"B",   # pin D15
}

# Textos que suelen salir en la descripción del puerto del ESP32 en Windows,
# según el chip USB de la placa (CP2102 o CH340/CH9102).
CHIPS_USB = ("CP210", "CH340", "CH910", "CH343", "SILICON LABS", "WCH", "USB-SERIAL", "USB SERIAL")


def listar_puertos():
    return list(list_ports.comports())


def buscar_puerto():
    """Busca solo el puerto del ESP32. Si no puede decidir, pide usar --puerto."""
    puertos = listar_puertos()
    candidatos = [
        p.device for p in puertos
        if any(chip in f"{p.description} {p.manufacturer or ''}".upper() for chip in CHIPS_USB)
    ]
    if len(candidatos) == 1:
        return candidatos[0]
    if not puertos:
        raise RuntimeError(
            "No encontré ningún puerto COM. Revisa que el ESP32 esté conectado, "
            "que el cable USB sea de datos (no solo de carga) y que el driver esté instalado."
        )
    lista = "\n".join(f"  {p.device}: {p.description}" for p in puertos)
    raise RuntimeError(
        "No pude saber cuál puerto es el ESP32. Estos son los que hay:\n"
        f"{lista}\nDímelo con --puerto, por ejemplo: --puerto COM5"
    )


def _abrir_puerto(puerto):
    ser = serial.Serial()
    ser.port = puerto
    ser.baudrate = BAUDIOS
    ser.timeout = 0.5
    # Con DTR y RTS apagados, abrir el puerto no reinicia el ESP32
    # ni lo deja atascado en modo de carga de programas.
    ser.dtr = False
    ser.rts = False
    try:
        ser.open()
    except serial.SerialException as error:
        raise RuntimeError(
            f"No pude abrir {puerto}. Si el Monitor Serie o el Serial Plotter del "
            f"Arduino IDE están abiertos, ciérralos y prueba otra vez. Detalle: {error}"
        )
    return ser


def _esperar_esp32(ser, intentos=12):
    """Manda 'P' hasta que el ESP32 conteste 'PONG' (por si se estaba reiniciando)."""
    for _ in range(intentos):
        ser.reset_input_buffer()
        ser.write(b"P")
        limite = time.time() + 0.5
        while time.time() < limite:
            if b"PONG" in ser.readline():
                return
    raise RuntimeError(
        "El ESP32 no responde. Revisa que tenga cargado el programa captura_audio "
        "y que el puerto sea el correcto (python codigo\\grabar_esp32.py --listar)."
    )


def recibir_muestras(microfono="max9814", puerto=None, al_empezar=None):
    """Pide una grabación al ESP32 con el micrófono elegido y devuelve (muestras, fs_real, atrasos)."""
    if microfono not in MICROFONOS:
        raise RuntimeError(f"Micrófono desconocido: {microfono}. Usa uno de: {', '.join(MICROFONOS)}")
    puerto = puerto or buscar_puerto()
    ser = _abrir_puerto(puerto)

    with ser:
        _esperar_esp32(ser)
        ser.timeout = 10
        if not al_empezar:
            # Cuenta regresiva en la terminal: así se puede tocar la nota justo
            # cuando empieza la grabación, y no un segundo tarde.
            print(f"Grabación con el {microfono.upper()}. Toca la nota cuando salga ¡YA!")
            for numero in (3, 2, 1):
                print(f"  {numero}...", flush=True)
                time.sleep(0.7)
        ser.write(MICROFONOS[microfono])

        while True:
            linea = ser.readline().decode("ascii", errors="ignore").strip()
            if not linea:
                raise RuntimeError(
                    "El ESP32 dejó de responder durante la grabación. Si acabas de cambiar "
                    "el programa, revisa que el ESP32 tenga cargada la versión nueva de captura_audio."
                )
            if linea == "GRABANDO":
                if al_empezar:
                    al_empezar()
                else:
                    print("  ¡YA! (grabando 2 s)", flush=True)
            elif linea.startswith("DATOS"):
                _, n, fs_real, atrasos = linea.split()
                n, fs_real, atrasos = int(n), float(fs_real), int(atrasos)
                break

        datos = ser.read(2 * n)

    if len(datos) != 2 * n:
        raise RuntimeError(
            f"Llegaron {len(datos)} de {2 * n} bytes. Prueba otra vez; si se repite, "
            "baja BAUDIOS a 115200 en este archivo y en el programa del ESP32."
        )

    # Cada muestra son 2 bytes (entero sin signo, orden little-endian, como en el ESP32)
    muestras = np.frombuffer(datos, dtype="<u2").astype(np.float32)
    return muestras, fs_real, atrasos


def revisar_senal(muestras, fs_real, atrasos):
    """Muestra en pantalla cómo llegó la señal y avisa si algo se ve mal."""
    minimo, maximo = int(muestras.min()), int(muestras.max())
    print(f"Señal recibida: {len(muestras)} muestras a {fs_real:.0f} Hz")
    print(
        f"Rango del ADC: {minimo} a {maximo} (de 0 a {MAX_ADC}), "
        f"aprox. {minimo / MAX_ADC * VREF_APROX:.2f} V a {maximo / MAX_ADC * VREF_APROX:.2f} V"
    )
    # Una o dos muestras en el límite no dañan el espectro; muchas sí.
    en_el_limite = int(np.sum((muestras <= 5) | (muestras >= MAX_ADC - 5)))
    if en_el_limite > 20:
        print(f"Aviso: la señal se saturó ({en_el_limite} muestras llegaron al límite del ADC). "
              "Aleja el instrumento o toca más suave.")
    if maximo - minimo < 100:
        print("Aviso: la señal es muy débil. Acerca el instrumento o revisa las conexiones del micrófono.")
    if atrasos > 0.05 * len(muestras) or fs_real < 0.97 * FS_OBJETIVO:
        print(
            f"Aviso: el ESP32 no alcanzó a medir a {FS_OBJETIVO} Hz (logró {fs_real:.0f} Hz). "
            "El .wav igual se guarda con la frecuencia real, pero conviene bajar FS en el "
            "programa del ESP32 (por ejemplo a 12000) y en FS_OBJETIVO de este archivo."
        )


def grabar_esp32(nombre_archivo, microfono="max9814", puerto=None, al_empezar=None):
    muestras, fs_real, atrasos = recibir_muestras(microfono, puerto, al_empezar)
    revisar_senal(muestras, fs_real, atrasos)

    # De números del ADC a señal de audio:
    # 1) quitar el nivel de reposo del micrófono (un voltaje fijo, no es sonido)
    audio = muestras - np.mean(muestras)
    # 2) normalizar igual que grabar_audio.py, para que el volumen no afecte la comparación
    audio = audio / (np.max(np.abs(audio)) + 1e-9)

    carpeta = os.path.dirname(nombre_archivo)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    sf.write(nombre_archivo, audio, int(round(fs_real)))
    print(f"Guardado en: {nombre_archivo}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graba 2 s con el ESP32 y los guarda como .wav")
    parser.add_argument("archivo", nargs="?", help="Nombre del .wav de salida")
    parser.add_argument("--micro", choices=list(MICROFONOS), default="max9814",
                        help="Micrófono con el que se graba (por defecto max9814)")
    parser.add_argument("--puerto", help="Puerto del ESP32, por ejemplo COM5 (si no se da, se busca solo)")
    parser.add_argument("--listar", action="store_true", help="Solo muestra los puertos disponibles")
    args = parser.parse_args()

    try:
        if args.listar:
            for p in listar_puertos():
                print(f"{p.device}: {p.description}")
        elif not args.archivo:
            parser.error("falta el nombre del .wav, por ejemplo referencias_max9814\\piano_1.wav")
        else:
            grabar_esp32(args.archivo, args.micro, args.puerto)
    except RuntimeError as error:
        print(f"Error: {error}")
        sys.exit(1)
