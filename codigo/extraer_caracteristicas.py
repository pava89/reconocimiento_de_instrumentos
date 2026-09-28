"""
PASO 3 — Extracción de características (documento: sección 4)
-----------------------------------------------------------------
De cada grabación se extraen los rasgos que el marco teórico identifica
como distintivos del timbre (sección 1.3 y 4):

  - f0: frecuencia fundamental                     (4.1)
  - armónicos: picos en múltiplos de f0            (4.1)
  - centroide: dónde se concentra la energía        (4.2)
  - energía: energía total de la señal              (2.1)

Esto convierte cada grabación en un vector numérico corto (un
"resumen" del espectro) que luego se puede comparar entre instrumentos.
"""

import numpy as np
import librosa


def frecuencia_fundamental(y, fs):
    # librosa.pyin estima f0 nota a nota; tomamos la mediana de los valores válidos
    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=fs
    )
    f0_validas = f0[~np.isnan(f0)]
    return float(np.median(f0_validas)) if len(f0_validas) > 0 else 0.0


def energia_armonicos(y, fs, f0, n_armonicos=6, tolerancia_hz=15):
    espectro = np.abs(np.fft.rfft(y))
    frecuencias = np.fft.rfftfreq(len(y), d=1 / fs)

    energias = []
    for k in range(1, n_armonicos + 1):
        objetivo = f0 * k
        ventana = (frecuencias > objetivo - tolerancia_hz) & (frecuencias < objetivo + tolerancia_hz)
        energias.append(float(espectro[ventana].max()) if ventana.any() else 0.0)

    # normalizar respecto al primer armónico (la fundamental) para comparar "forma", no volumen
    if energias[0] > 0:
        energias = [e / energias[0] for e in energias]
    return energias


def extraer_caracteristicas(ruta_audio: str) -> dict:
    y, fs = librosa.load(ruta_audio, sr=None)

    f0 = frecuencia_fundamental(y, fs)
    armonicos = energia_armonicos(y, fs, f0) if f0 > 0 else [0.0] * 6
    centroide = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=fs)))
    energia_total = float(np.sum(y ** 2))

    return {
        "archivo": ruta_audio,
        "f0": f0,
        "armonicos": armonicos,
        "centroide": centroide,
        "energia_total": energia_total,
    }


if __name__ == "__main__":
    import sys
    caracteristicas = extraer_caracteristicas(sys.argv[1])
    for clave, valor in caracteristicas.items():
        print(f"{clave}: {valor}")
