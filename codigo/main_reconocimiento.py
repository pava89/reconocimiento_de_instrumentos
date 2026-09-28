"""
PASO 5 — Prototipo completo de Etapa 1
-----------------------------------------------------------------
Flujo:
  1) Construye (o carga) el banco de referencia con muestras ya grabadas
     de tus instrumentos (piano, guitarra, flauta).
  2) Graba una muestra nueva desde el micrófono.
  3) Extrae sus características y la compara contra el banco.
  4) Imprime el instrumento reconocido.

IMPORTANTE: este script se ejecuta desde la carpeta raíz del proyecto
(proyecto_instrumentos/), no desde dentro de codigo/, para que las rutas
"referencias/..." se encuentren bien:
    python codigo/main_reconocimiento.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_caracteristicas import extraer_caracteristicas
from clasificador import construir_banco, guardar_banco, cargar_banco, clasificar
from grabar_audio import grabar

MUESTRAS_POR_INSTRUMENTO = {
    "piano": ["referencias/piano_1.wav", "referencias/piano_2.wav"],
    "guitarra": ["referencias/guitarra_1.wav", "referencias/guitarra_2.wav"],
    "flauta": ["referencias/flauta_1.wav", "referencias/flauta_2.wav"],
    "voz": ["referencias/voz_1.wav", "referencias/voz_2.wav"],
}


def preparar_banco(ruta_banco="banco_referencia.json"):
    if os.path.exists(ruta_banco):
        return cargar_banco(ruta_banco)
    banco = construir_banco(MUESTRAS_POR_INSTRUMENTO, extraer_caracteristicas)
    guardar_banco(banco, ruta_banco)
    return banco


if __name__ == "__main__":
    banco = preparar_banco()
    print("Banco de referencia listo:", list(banco.keys()))

    archivo_nuevo = "muestra_nueva.wav"
    grabar(archivo_nuevo, duracion=2.0)

    caracteristicas = extraer_caracteristicas(archivo_nuevo)
    instrumento = clasificar(caracteristicas, banco)

    print(f"\nInstrumento reconocido: {instrumento}")
