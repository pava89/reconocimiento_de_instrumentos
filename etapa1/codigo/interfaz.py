"""
INTERFAZ — Ventana simple que muestra el instrumento reconocido
-----------------------------------------------------------------
Usa tkinter (viene incluido con Python, no requiere instalar nada).
Reutiliza exactamente el mismo pipeline de main_reconocimiento.py:
graba -> extrae características -> compara contra el banco -> muestra
el resultado en grande, en vez de solo en la terminal.

Ejecutar desde la carpeta raíz del proyecto:
    python codigo\\interfaz.py
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grabar_audio import grabar
from extraer_caracteristicas import extraer_caracteristicas
from clasificador import construir_banco, guardar_banco, cargar_banco, clasificar
from main_reconocimiento import MUESTRAS_POR_INSTRUMENTO

# Un emoji por instrumento; si agregas uno nuevo al diccionario y no está
# aquí, se muestra una nota musical genérica.
ICONOS = {
    "piano": "🎹",
    "guitarra": "🎸",
    "flauta": "🪈",
    "voz": "🎤",
}


def preparar_banco(ruta_banco="banco_referencia.json"):
    if os.path.exists(ruta_banco):
        return cargar_banco(ruta_banco)
    banco = construir_banco(MUESTRAS_POR_INSTRUMENTO, extraer_caracteristicas)
    guardar_banco(banco, ruta_banco)
    return banco


class Interfaz:
    def __init__(self, root, banco):
        self.banco = banco
        root.title("Reconocimiento de instrumentos")
        root.geometry("360x280")
        root.configure(bg="#1e1e2e")

        self.icono = tk.Label(root, text="🎵", font=("Segoe UI Emoji", 80), bg="#1e1e2e", fg="white")
        self.icono.pack(pady=(30, 10))

        self.resultado = tk.Label(root, text="Presiona el botón y toca una nota", font=("Segoe UI", 14),
                                   bg="#1e1e2e", fg="white", wraplength=320, justify="center")
        self.resultado.pack(pady=10)

        self.boton = tk.Button(root, text="Grabar y reconocer", font=("Segoe UI", 12),
                                command=self.grabar_y_reconocer, bg="#89b4fa", fg="#1e1e2e",
                                relief="flat", padx=15, pady=8)
        self.boton.pack(pady=10)

    def grabar_y_reconocer(self):
        self.resultado.config(text="Grabando... toca la nota ahora")
        self.icono.config(text="🎙️")
        self.boton.update_idletasks()  # refresca la ventana antes de grabar (bloqueante)

        archivo = "muestra_nueva.wav"
        grabar(archivo, duracion=2.0)

        caracteristicas = extraer_caracteristicas(archivo)
        instrumento = clasificar(caracteristicas, self.banco)

        self.icono.config(text=ICONOS.get(instrumento, "🎵"))
        self.resultado.config(text=f"Instrumento reconocido:\n{instrumento.upper()}")


if __name__ == "__main__":
    banco = preparar_banco()
    root = tk.Tk()
    app = Interfaz(root, banco)
    root.mainloop()
