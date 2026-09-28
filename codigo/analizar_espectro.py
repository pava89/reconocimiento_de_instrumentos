"""
PASO 2 — Transformada de Fourier y espectro (documento: sección 3.1 y 3.2)
---------------------------------------------------------------------------
Carga un .wav grabado en el paso 1, le aplica la FFT y grafica el
espectro de magnitud (energía por frecuencia). Esta gráfica es
exactamente lo que el marco teórico describe en 3.2: "una gráfica que
muestra cuánta energía hay en cada frecuencia".

Uso:
    python analizar_espectro.py violin_nota1.wav
"""

import sys
import numpy as np
import librosa
import matplotlib.pyplot as plt


def calcular_espectro(ruta_audio: str):
    y, fs = librosa.load(ruta_audio, sr=None)  # sr=None respeta la frecuencia original

    n = len(y)
    espectro = np.fft.rfft(y)                     # FFT solo de la mitad útil (señal real)
    magnitud = np.abs(espectro) / n                # energía relativa (sección 2.1)
    frecuencias = np.fft.rfftfreq(n, d=1 / fs)     # eje de frecuencias en Hz

    return frecuencias, magnitud, fs


def graficar(frecuencias, magnitud, titulo="Espectro", freq_max=5000):
    plt.figure(figsize=(9, 4))
    plt.plot(frecuencias, magnitud)
    plt.xlim(0, freq_max)
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("Magnitud")
    plt.title(titulo)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    ruta = sys.argv[1]
    frecuencias, magnitud, fs = calcular_espectro(ruta)
    graficar(frecuencias, magnitud, titulo=f"Espectro de {ruta}")
