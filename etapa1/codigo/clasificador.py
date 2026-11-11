"""
PASO 4 — Comparación y reconocimiento (documento: sección 5)
-----------------------------------------------------------------
Construye un banco de referencia {instrumento: vector_promedio} y
clasifica una muestra nueva por la distancia (5.2) a cada instrumento
del banco: se elige el más parecido (5.1).
"""

import json
import numpy as np


def vectorizar(caracteristicas: dict) -> np.ndarray:
    """Convierte el dict de extraer_caracteristicas.py en un vector plano,
    normalizando cada característica para que ninguna domine por su escala."""
    f0_norm = caracteristicas["f0"] / 500.0
    centroide_norm = caracteristicas["centroide"] / 3000.0
    return np.array([f0_norm, centroide_norm, *caracteristicas["armonicos"]])

def construir_banco(muestras_por_instrumento: dict, extractor) -> dict:
    """
    muestras_por_instrumento: {"violin": ["v1.wav", "v2.wav"], "piano": [...], ...}
    extractor: función extraer_caracteristicas() del paso 3
    """
    banco = {}
    for instrumento, archivos in muestras_por_instrumento.items():
        vectores = [vectorizar(extractor(a)) for a in archivos]
        banco[instrumento] = np.mean(vectores, axis=0).tolist()
    return banco


def guardar_banco(banco: dict, ruta="banco_referencia.json"):
    with open(ruta, "w") as f:
        json.dump(banco, f, indent=2)


def cargar_banco(ruta="banco_referencia.json") -> dict:
    with open(ruta) as f:
        return json.load(f)


def clasificar(caracteristicas_nueva: dict, banco: dict) -> str:
    vector_nuevo = vectorizar(caracteristicas_nueva)
    mejor_instrumento, menor_distancia = None, float("inf")

    for instrumento, vector_ref in banco.items():
        distancia = np.linalg.norm(vector_nuevo - np.array(vector_ref))
        if distancia < menor_distancia:
            mejor_instrumento, menor_distancia = instrumento, distancia

    return mejor_instrumento
