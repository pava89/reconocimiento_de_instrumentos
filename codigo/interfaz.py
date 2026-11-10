"""
INTERFAZ — Ventana simple que muestra el instrumento reconocido
-----------------------------------------------------------------
Usa tkinter (viene incluido con Python, no requiere instalar nada).
Reutiliza exactamente el mismo flujo de main_reconocimiento.py:
graba -> extrae características -> compara contra el banco -> muestra
el resultado en grande, en vez de solo en la terminal.

Ejecutar desde la carpeta raíz del proyecto:
    python codigo\\interfaz.py                  (Etapa 1, micrófono del PC)
    python codigo\\interfaz.py --fuente max9814   (Etapa 2)
    python codigo\\interfaz.py --fuente max4466   (Etapa 2)
"""

import argparse
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_caracteristicas import extraer_caracteristicas
from clasificador import clasificar
from main_reconocimiento import FUENTES, FUENTES_ESP32, preparar_banco, grabar_muestra

# Un emoji por instrumento; si agregas uno nuevo al diccionario y no está
# aquí, se muestra una nota musical genérica.
ICONOS = {
    "piano": "🎹",
    "guitarra": "🎸",
    "flauta": "🪈",
    "voz": "🎤",
}

NOMBRE_FUENTE = {
    "pc": "micrófono del PC",
    "max9814": "ESP32 + MAX9814",
    "max4466": "ESP32 + MAX4466",
}


class Interfaz:
    def __init__(self, root, banco, fuente="pc", puerto=None):
        self.root = root
        self.banco = banco
        self.fuente = fuente
        self.puerto = puerto

        root.title(f"Reconocimiento de instrumentos ({NOMBRE_FUENTE[fuente]})")
        root.geometry("380x300")
        root.configure(bg="#1e1e2e")

        self.icono = tk.Label(root, text="🎵", font=("Segoe UI Emoji", 80), bg="#1e1e2e", fg="white")
        self.icono.pack(pady=(30, 10))

        self.resultado = tk.Label(root, text="Presiona el botón y toca una nota", font=("Segoe UI", 14),
                                  bg="#1e1e2e", fg="white", wraplength=340, justify="center")
        self.resultado.pack(pady=10)

        self.boton = tk.Button(root, text="Grabar y reconocer", font=("Segoe UI", 12),
                               command=self.grabar_y_reconocer, bg="#89b4fa", fg="#1e1e2e",
                               relief="flat", padx=15, pady=8)
        self.boton.pack(pady=10)

    def mostrar(self, icono, texto):
        self.icono.config(text=icono)
        self.resultado.config(text=texto)
        self.root.update_idletasks()  # refresca la ventana antes de seguir (grabar bloquea)

    def grabar_y_reconocer(self):
        if self.fuente in FUENTES_ESP32:
            self.mostrar("🔌", "Conectando con el ESP32...")

        archivo = "muestra_nueva.wav"
        try:
            grabar_muestra(archivo, self.fuente, self.puerto,
                           al_empezar=lambda: self.mostrar("🎙️", "Grabando... toca la nota ahora"))
        except RuntimeError as error:
            self.mostrar("⚠️", f"Error: {error}")
            return

        caracteristicas = extraer_caracteristicas(archivo)
        instrumento = clasificar(caracteristicas, self.banco)
        self.mostrar(ICONOS.get(instrumento, "🎵"), f"Instrumento reconocido:\n{instrumento.upper()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente", choices=list(FUENTES), default="pc",
                        help="pc = micrófono del computador; max9814 / max4466 = micrófonos del ESP32")
    parser.add_argument("--puerto", help="Puerto del ESP32, por ejemplo COM5 (si no se da, se busca solo)")
    args = parser.parse_args()

    banco = preparar_banco(args.fuente)
    root = tk.Tk()
    app = Interfaz(root, banco, args.fuente, args.puerto)
    root.mainloop()
