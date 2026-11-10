"""
EVALUACIÓN — pruebas de acierto con una fuente (Etapa 1 o Etapa 2)
--------------------------------------------------------------------
Hace las pruebas por ti y lleva la cuenta de los aciertos:
  1) Te dice qué instrumento tocar y cuántas pruebas faltan.
  2) En cada prueba presionas Enter, tocas la nota y el programa
     graba, reconoce y te dice si acertó.
  3) Cada prueba se guarda en resultados/resultados_<fuente>.csv y el
     audio en resultados/<fuente>/ (sirve para el informe).
  4) Al final muestra la tabla de aciertos y la matriz de confusión.

Uso (desde la carpeta raíz del proyecto):
    python codigo\\evaluar.py --fuente max9814                  (15 pruebas por instrumento)
    python codigo\\evaluar.py --fuente max4466 --pruebas 15
    python codigo\\evaluar.py --fuente max9814 --instrumento flauta   (solo un instrumento)
    python codigo\\evaluar.py --fuente max9814 --resumen         (solo ver la tabla)

Durante las pruebas:
    Enter  -> grabar la siguiente prueba
    d      -> descartar la última prueba (por ejemplo si no tocaste a tiempo)
    q      -> salir (lo hecho queda guardado; puedes seguir después)
"""

import argparse
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_caracteristicas import extraer_caracteristicas
from clasificador import clasificar
from main_reconocimiento import FUENTES, preparar_banco, grabar_muestra

CARPETA = "resultados"
COLUMNAS = ["fecha", "fuente", "instrumento_real", "instrumento_reconocido", "acierto",
            "f0", "centroide", "archivo"]


def ruta_csv(fuente):
    return os.path.join(CARPETA, f"resultados_{fuente}.csv")


def leer_resultados(fuente):
    if not os.path.exists(ruta_csv(fuente)):
        return []
    with open(ruta_csv(fuente), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escribir_resultados(fuente, filas):
    os.makedirs(CARPETA, exist_ok=True)
    with open(ruta_csv(fuente), "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)


def mostrar_resumen(fuente, instrumentos):
    filas = leer_resultados(fuente)
    if not filas:
        print(f"Todavía no hay pruebas guardadas para '{fuente}'.")
        return

    print(f"\nResultados con la fuente '{fuente}'")
    print(f"{'Instrumento':<12}{'Aciertos':>10}{'Intentos':>10}{'Acierto':>10}")
    total_aciertos = total = 0
    for instrumento in instrumentos:
        propias = [f for f in filas if f["instrumento_real"] == instrumento]
        aciertos = sum(f["acierto"] == "1" for f in propias)
        total_aciertos += aciertos
        total += len(propias)
        porcentaje = f"{100 * aciertos / len(propias):.1f} %" if propias else "-"
        print(f"{instrumento:<12}{aciertos:>10}{len(propias):>10}{porcentaje:>10}")
    porcentaje = f"{100 * total_aciertos / total:.1f} %" if total else "-"
    print(f"{'Total':<12}{total_aciertos:>10}{total:>10}{porcentaje:>10}")

    # Matriz de confusión: filas = lo que se tocó, columnas = lo que reconoció el programa
    print("\nMatriz de confusión (filas: lo que se tocó; columnas: lo que reconoció)")
    print(f"{'':<12}" + "".join(f"{i:>10}" for i in instrumentos))
    for real in instrumentos:
        conteos = [sum(f["instrumento_real"] == real and f["instrumento_reconocido"] == pred for f in filas)
                   for pred in instrumentos]
        print(f"{real:<12}" + "".join(f"{c:>10}" for c in conteos))


def evaluar(fuente, instrumentos, pruebas, puerto):
    banco = preparar_banco(fuente)
    filas = leer_resultados(fuente)
    carpeta_audio = os.path.join(CARPETA, fuente)
    os.makedirs(carpeta_audio, exist_ok=True)

    for instrumento in instrumentos:
        hechas = sum(f["instrumento_real"] == instrumento for f in filas)
        if hechas >= pruebas:
            print(f"\n{instrumento.upper()}: ya tiene {hechas} pruebas, se salta.")
            continue

        print(f"\n=== {instrumento.upper()} ({hechas} de {pruebas} hechas) ===")
        while hechas < pruebas:
            orden = input(f"Prueba {hechas + 1}/{pruebas} de {instrumento.upper()}: "
                          "Enter para grabar, 'd' descarta la última, 'q' sale > ").strip().lower()
            if orden == "q":
                escribir_resultados(fuente, filas)
                print("Guardado. Puedes seguir después con el mismo comando.")
                mostrar_resumen(fuente, instrumentos)
                return
            if orden == "d":
                propias = [i for i, f in enumerate(filas) if f["instrumento_real"] == instrumento]
                if propias:
                    quitada = filas.pop(propias[-1])
                    hechas -= 1
                    escribir_resultados(fuente, filas)
                    print(f"Descartada la prueba que dio '{quitada['instrumento_reconocido']}'.")
                else:
                    print("No hay pruebas de este instrumento para descartar.")
                continue

            archivo = os.path.join(carpeta_audio, f"{instrumento}_{hechas + 1:02d}.wav")
            try:
                grabar_muestra(archivo, fuente, puerto)
            except RuntimeError as error:
                print(f"Error: {error}")
                continue

            caracteristicas = extraer_caracteristicas(archivo)
            reconocido = clasificar(caracteristicas, banco)
            acierto = reconocido == instrumento
            filas.append({
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "fuente": fuente,
                "instrumento_real": instrumento,
                "instrumento_reconocido": reconocido,
                "acierto": "1" if acierto else "0",
                "f0": f"{caracteristicas['f0']:.1f}",
                "centroide": f"{caracteristicas['centroide']:.1f}",
                "archivo": archivo.replace("\\", "/"),
            })
            escribir_resultados(fuente, filas)   # se guarda en cada prueba, por si algo se corta
            hechas += 1
            marca = "✓ ACIERTO" if acierto else f"✗ FALLO (dijo {reconocido})"
            print(f"  {marca}   f0 = {caracteristicas['f0']:.1f} Hz")

    mostrar_resumen(fuente, instrumentos)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pruebas de acierto con conteo automático")
    parser.add_argument("--fuente", choices=list(FUENTES), required=True,
                        help="pc, max9814 o max4466")
    parser.add_argument("--pruebas", type=int, default=15, help="Pruebas por instrumento (por defecto 15)")
    parser.add_argument("--instrumento", help="Hacer solo este instrumento")
    parser.add_argument("--puerto", help="Puerto del ESP32, por ejemplo COM5 (si no se da, se busca solo)")
    parser.add_argument("--resumen", action="store_true", help="Solo mostrar la tabla de resultados")
    args = parser.parse_args()

    todos = list(FUENTES[args.fuente][0].keys())
    if args.instrumento and args.instrumento not in todos:
        sys.exit(f"Instrumento desconocido: {args.instrumento}. Opciones: {', '.join(todos)}")
    elegidos = [args.instrumento] if args.instrumento else todos

    if args.resumen:
        mostrar_resumen(args.fuente, todos)
    else:
        evaluar(args.fuente, elegidos, args.pruebas, args.puerto)
