"""
GRÁFICAS — genera todas las figuras del informe y las guarda en graficas/
--------------------------------------------------------------------------
Lee las grabaciones de referencia y los CSV de resultados y produce:

  graficas/<fuente>/<instrumento>_<n>.png
      Forma de onda (tiempo) y espectro (FFT) de cada grabación de referencia.
      <fuente> es pc (Etapa 1), max9814 o max4466 (Etapa 2).

  graficas/comparacion/espectro_<instrumento>.png
      El espectro del mismo instrumento con las tres fuentes, uno debajo del
      otro, para ver cómo cambia según el micrófono.

  graficas/comparacion/acierto_por_fuente.png
      Porcentaje de acierto por instrumento y fuente (micrófono del PC,
      MAX9814 y MAX4466).

  graficas/comparacion/matriz_confusion_<fuente>.png
      Qué se tocó contra qué reconoció el programa, en las pruebas de la Etapa 2.

Solo usa numpy, soundfile y matplotlib (no librosa), así que no depende de
numba. Se ejecuta desde la carpeta raíz del proyecto:
    python codigo\\generar_graficas.py
"""

import csv
import os

import matplotlib

matplotlib.use("Agg")  # guarda las imágenes sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

SALIDA = "graficas"
FREQ_MAX = 5000  # Hz que se muestran en los espectros (los armónicos útiles están ahí)

FUENTES = {
    "pc": ("Micrófono del PC (Etapa 1)", "referencias"),
    "max9814": ("ESP32 + MAX9814", "referencias_max9814"),
    "max4466": ("ESP32 + MAX4466", "referencias_max4466"),
}
INSTRUMENTOS = ["piano", "guitarra", "flauta"]
INSTRUMENTOS_PC = ["piano", "guitarra", "flauta", "voz"]

# Resultados de la Etapa 1 (16 pruebas por instrumento, ver README)
ETAPA1 = {"piano": (16, 16), "guitarra": (14, 16), "flauta": (16, 16)}

# Un color fijo por fuente, el mismo en todas las gráficas
COLOR = {"pc": "#2a78d6", "max9814": "#eb6834", "max4466": "#1baf7a"}
FONDO = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
REJILLA = "#e4e3df"
AZULES = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "axes.edgecolor": REJILLA, "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO,
    "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "text.color": TEXTO,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
})


def espectro(ruta):
    y, fs = sf.read(ruta)
    if y.ndim > 1:
        y = y.mean(axis=1)
    y = y - np.mean(y)
    magnitud = np.abs(np.fft.rfft(y)) / len(y)
    frecuencias = np.fft.rfftfreq(len(y), d=1 / fs)
    return y, fs, frecuencias, magnitud


def pico_principal(frecuencias, magnitud):
    """Frecuencia con más energía entre 50 Hz y FREQ_MAX (solo para rotular)."""
    zona = (frecuencias > 50) & (frecuencias < FREQ_MAX)
    return frecuencias[zona][np.argmax(magnitud[zona])]


def guardar(fig, *partes):
    ruta = os.path.join(SALIDA, *partes)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ", ruta.replace("\\", "/"))


def graficas_referencias():
    print("Referencias (forma de onda + espectro):")
    for fuente, (nombre, carpeta) in FUENTES.items():
        instrumentos = INSTRUMENTOS_PC if fuente == "pc" else INSTRUMENTOS
        for instrumento in instrumentos:
            for n in (1, 2):
                ruta = os.path.join(carpeta, f"{instrumento}_{n}.wav")
                if not os.path.exists(ruta):
                    continue
                y, fs, f, m = espectro(ruta)
                t = np.arange(len(y)) / fs
                fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.5))
                fig.suptitle(f"{instrumento.capitalize()} {n} — {nombre}", fontweight="bold")
                a1.plot(t, y, color=COLOR[fuente], linewidth=0.6)
                a1.set_xlabel("Tiempo (s)")
                a1.set_ylabel("Amplitud")
                a1.set_title("Forma de onda", fontsize=10, fontweight="normal", color=TEXTO_2, loc="left")
                a2.plot(f, m, color=COLOR[fuente], linewidth=0.8)
                a2.set_xlim(0, FREQ_MAX)
                a2.set_xlabel("Frecuencia (Hz)")
                a2.set_ylabel("Magnitud")
                a2.set_title(f"Espectro (FFT) — pico principal en {pico_principal(f, m):.0f} Hz",
                             fontsize=10, fontweight="normal", color=TEXTO_2, loc="left")
                fig.tight_layout()
                guardar(fig, fuente, f"{instrumento}_{n}.png")


def graficas_espectros_comparados():
    print("Espectros comparados por instrumento:")
    for instrumento in INSTRUMENTOS:
        fig, ejes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
        fig.suptitle(f"{instrumento.capitalize()}: espectro con cada micrófono "
                     "(promedio de las 2 referencias, normalizado)", fontweight="bold")
        for eje, (fuente, (nombre, carpeta)) in zip(ejes, FUENTES.items()):
            espectros = []
            for n in (1, 2):
                ruta = os.path.join(carpeta, f"{instrumento}_{n}.wav")
                if os.path.exists(ruta):
                    _, _, f, m = espectro(ruta)
                    espectros.append(np.interp(np.arange(0, FREQ_MAX, 1.0), f, m))
            if not espectros:
                continue
            promedio = np.mean(espectros, axis=0)
            promedio /= promedio.max()
            eje.plot(np.arange(0, FREQ_MAX, 1.0), promedio, color=COLOR[fuente], linewidth=0.8)
            eje.set_ylim(0, 1.08)
            eje.set_ylabel("Magnitud")
            eje.set_title(nombre, fontsize=10, fontweight="normal", color=TEXTO_2, loc="left")
        ejes[-1].set_xlabel("Frecuencia (Hz)")
        ejes[-1].set_xlim(0, FREQ_MAX)
        fig.tight_layout()
        guardar(fig, "comparacion", f"espectro_{instrumento}.png")


def leer_resultados(fuente):
    ruta = os.path.join("resultados", f"resultados_{fuente}.csv")
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def grafica_acierto():
    print("Acierto por fuente:")
    datos = {"pc": ETAPA1}
    for fuente in ("max9814", "max4466"):
        filas = leer_resultados(fuente)
        datos[fuente] = {
            i: (sum(f["acierto"] == "1" for f in filas if f["instrumento_real"] == i),
                sum(f["instrumento_real"] == i for f in filas))
            for i in INSTRUMENTOS
        }
    grupos = INSTRUMENTOS + ["total"]
    fig, eje = plt.subplots(figsize=(9, 4.8))
    ancho = 0.26
    x = np.arange(len(grupos))
    for k, (fuente, (nombre, _)) in enumerate(FUENTES.items()):
        valores = []
        for g in grupos:
            if g == "total":
                aciertos = sum(datos[fuente][i][0] for i in INSTRUMENTOS)
                intentos = sum(datos[fuente][i][1] for i in INSTRUMENTOS)
            else:
                aciertos, intentos = datos[fuente][g]
            valores.append(100 * aciertos / intentos if intentos else 0)
        posiciones = x + (k - 1) * ancho
        barras = eje.bar(posiciones, valores, ancho - 0.03, color=COLOR[fuente], label=nombre)
        for barra, valor in zip(barras, valores):
            eje.text(barra.get_x() + barra.get_width() / 2, valor + 1.2, f"{valor:.1f}",
                     ha="center", va="bottom", fontsize=8, color=TEXTO)
    eje.set_xticks(x, [g.capitalize() for g in grupos])
    eje.set_ylim(0, 112)
    eje.set_ylabel("Acierto (%)")
    eje.grid(axis="x", visible=False)
    eje.set_title("Porcentaje de acierto por instrumento y micrófono", loc="left")
    eje.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=9)
    fig.text(0.01, -0.08, "Etapa 1: 16 pruebas por instrumento (solo piano, guitarra y flauta). "
             "Etapa 2: 15 pruebas por instrumento y micrófono.", fontsize=8, color=TEXTO_2)
    fig.tight_layout()
    guardar(fig, "comparacion", "acierto_por_fuente.png")


def matrices_confusion():
    print("Matrices de confusión:")
    for fuente in ("max9814", "max4466"):
        filas = leer_resultados(fuente)
        if not filas:
            continue
        matriz = np.array([[sum(f["instrumento_real"] == r and f["instrumento_reconocido"] == p for f in filas)
                            for p in INSTRUMENTOS] for r in INSTRUMENTOS])
        fig, eje = plt.subplots(figsize=(5.2, 4.4))
        mapa = matplotlib.colors.ListedColormap(AZULES)
        eje.imshow(matriz, cmap=mapa, vmin=0, vmax=max(15, matriz.max()))
        eje.grid(False)
        for r in range(3):
            for p in range(3):
                valor = matriz[r, p]
                eje.text(p, r, str(valor), ha="center", va="center", fontsize=13, fontweight="bold",
                         color="white" if valor >= 8 else TEXTO)
        etiquetas = [i.capitalize() for i in INSTRUMENTOS]
        eje.set_xticks(range(3), etiquetas)
        eje.set_yticks(range(3), etiquetas)
        eje.set_xlabel("Lo que reconoció el programa")
        eje.set_ylabel("Lo que se tocó")
        aciertos = int(np.trace(matriz))
        eje.set_title(f"{FUENTES[fuente][0]}: {aciertos}/{matriz.sum()} aciertos", loc="left")
        for lado in eje.spines.values():
            lado.set_visible(False)
        fig.tight_layout()
        guardar(fig, "comparacion", f"matriz_confusion_{fuente}.png")


if __name__ == "__main__":
    graficas_referencias()
    graficas_espectros_comparados()
    grafica_acierto()
    matrices_confusion()
    print(f"Listo. Todas las gráficas quedaron en la carpeta {SALIDA}/")
