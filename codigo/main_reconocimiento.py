"""
PASO 5 — Prototipo completo (Etapa 1 y Etapa 2)
-----------------------------------------------------------------
Flujo:
  1) Construye (o carga) el banco de referencia con muestras ya grabadas.
  2) Graba una muestra nueva con la fuente elegida:
       pc       -> micrófono del computador (Etapa 1)
       max9814  -> ESP32 + MAX9814 (Etapa 2)
       max4466  -> ESP32 + MAX4466 (Etapa 2)
  3) Extrae sus características y la compara contra el banco.
  4) Imprime el instrumento reconocido.

Cada micrófono cambia el espectro, así que cada fuente tiene su propio
banco y sus propias grabaciones de referencia.

IMPORTANTE: se ejecuta desde la carpeta raíz del proyecto
(proyecto_instrumentos/), no desde dentro de codigo/:
    python codigo\\main_reconocimiento.py                    (micrófono del PC)
    python codigo\\main_reconocimiento.py --fuente max9814
    python codigo\\main_reconocimiento.py --fuente max4466
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_caracteristicas import extraer_caracteristicas
from clasificador import construir_banco, guardar_banco, cargar_banco, clasificar
from grabar_audio import grabar

# Etapa 1 (micrófono del PC): 4 instrumentos, tal como se entregó
MUESTRAS_POR_INSTRUMENTO = {
    "piano": ["referencias/piano_1.wav", "referencias/piano_2.wav"],
    "guitarra": ["referencias/guitarra_1.wav", "referencias/guitarra_2.wav"],
    "flauta": ["referencias/flauta_1.wav", "referencias/flauta_2.wav"],
    "voz": ["referencias/voz_1.wav", "referencias/voz_2.wav"],
}

# Etapa 2 (ESP32): 3 instrumentos, 2 grabaciones de referencia cada uno
INSTRUMENTOS_ESP32 = ["piano", "guitarra", "flauta"]
REFERENCIAS_POR_INSTRUMENTO = 2


def muestras_esp32(microfono):
    carpeta = f"referencias_{microfono}"
    return {
        instrumento: [f"{carpeta}/{instrumento}_{k}.wav" for k in range(1, REFERENCIAS_POR_INSTRUMENTO + 1)]
        for instrumento in INSTRUMENTOS_ESP32
    }


# fuente -> (grabaciones de referencia, archivo donde se guarda su banco)
FUENTES = {
    "pc": (MUESTRAS_POR_INSTRUMENTO, "banco_referencia.json"),
    "max9814": (muestras_esp32("max9814"), "banco_max9814.json"),
    "max4466": (muestras_esp32("max4466"), "banco_max4466.json"),
}
FUENTES_ESP32 = ("max9814", "max4466")


def preparar_banco(fuente="pc"):
    muestras, ruta_banco = FUENTES[fuente]
    if os.path.exists(ruta_banco):
        return cargar_banco(ruta_banco)

    faltantes = [archivo for archivos in muestras.values() for archivo in archivos
                 if not os.path.exists(archivo)]
    if faltantes:
        if fuente in FUENTES_ESP32:
            script = f"grabar_esp32.py --micro {fuente}"
        else:
            script = "grabar_audio.py"
        rutas_windows = [archivo.replace("/", "\\") for archivo in faltantes]
        comandos = "\n".join(f"  python codigo\\{script} {ruta}" for ruta in rutas_windows)
        sys.exit(f"Faltan grabaciones de referencia para '{fuente}'. Grábalas primero:\n{comandos}")

    banco = construir_banco(muestras, extraer_caracteristicas)
    guardar_banco(banco, ruta_banco)
    return banco


def grabar_muestra(archivo, fuente="pc", puerto=None, al_empezar=None):
    if fuente in FUENTES_ESP32:
        # Se importa aquí para que la Etapa 1 funcione aunque no esté instalado pyserial
        from grabar_esp32 import grabar_esp32
        grabar_esp32(archivo, microfono=fuente, puerto=puerto, al_empezar=al_empezar)
    else:
        if al_empezar:
            al_empezar()
        grabar(archivo, duracion=2.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente", choices=list(FUENTES), default="pc",
                        help="pc = micrófono del computador; max9814 / max4466 = micrófonos del ESP32")
    parser.add_argument("--puerto", help="Puerto del ESP32, por ejemplo COM5 (si no se da, se busca solo)")
    args = parser.parse_args()

    banco = preparar_banco(args.fuente)
    print(f"Fuente: {args.fuente}. Banco de referencia listo:", list(banco.keys()))

    archivo_nuevo = "muestra_nueva.wav"
    try:
        grabar_muestra(archivo_nuevo, args.fuente, args.puerto)
    except RuntimeError as error:
        sys.exit(f"Error: {error}")

    caracteristicas = extraer_caracteristicas(archivo_nuevo)
    instrumento = clasificar(caracteristicas, banco)

    print(f"\nInstrumento reconocido: {instrumento}")
