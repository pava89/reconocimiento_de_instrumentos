"""
PASO 1 — Captura de audio (Etapa 1 del proyecto)
--------------------------------------------------
Graba un fragmento corto desde el micrófono del computador y lo guarda
como archivo .wav. Esto reemplaza, por ahora, al Arduino/ESP32 que se
usará en la Etapa 2: aquí la "conversión de la onda sonora a números"
la hace directamente la tarjeta de sonido del computador.

Uso:
    python grabar_audio.py violin_nota1.wav
    python grabar_audio.py piano_nota1.wav --duracion 3
"""

import sys
import argparse
import numpy as np
import sounddevice as sd
import soundfile as sf

FRECUENCIA_MUESTREO = 44100  # Hz — estándar de audio (documento: sección 2.1, "señal periódica")


def grabar(nombre_archivo: str, duracion: float = 2.0, fs: int = FRECUENCIA_MUESTREO):
    print(f"Grabando {duracion} s a {fs} Hz... toca la nota ahora.")
    audio = sd.rec(int(duracion * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()  # espera a que termine la grabación
    audio = audio.flatten()

    # Normalizar para que el volumen no afecte la comparación de espectros (sección 5.1)
    pico = np.max(np.abs(audio)) + 1e-9
    audio = audio / pico

    sf.write(nombre_archivo, audio, fs)
    print(f"Guardado en: {nombre_archivo}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo", help="Nombre del .wav de salida")
    parser.add_argument("--duracion", type=float, default=2.0)
    args = parser.parse_args()
    grabar(args.archivo, args.duracion)
