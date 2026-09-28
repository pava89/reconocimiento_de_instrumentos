# Reconocimiento de instrumentos — Etapa 1

Proyecto de Teoría de Señales: reconoce si una nota fue tocada en
**piano**, **guitarra** o **flauta**, usando el micrófono del computador
y análisis espectral (FFT).

## Estructura de carpetas

```
proyecto_instrumentos/
├── README.md
├── requirements.txt
├── referencias/              ← aquí se guardan los .wav de cada instrumento
└── codigo/
    ├── grabar_audio.py        (Paso 1: graba desde el micrófono)
    ├── analizar_espectro.py   (Paso 2: FFT y gráfica del espectro)
    ├── extraer_caracteristicas.py  (Paso 3: f0, armónicos, centroide)
    ├── clasificador.py        (Paso 4: banco de referencia y comparación)
    └── main_reconocimiento.py (Paso 5: todo junto, en vivo)
```

`referencias/` y `codigo/` están separadas a propósito: `codigo/` es lo
que sube a GitHub como "el programa"; `referencias/` son tus datos
(grabaciones), que normalmente NO se sube a GitHub (pesan mucho y no es
código). De eso hablamos en el paso de GitHub.

## 1. Instalar Visual Studio Code + Python (una sola vez)

Asumo que "Visual Studios" es **Visual Studio Code** (el editor liviano,
no el "Visual Studio" grande de C#/C++ — son programas distintos). Si
tienes el grande, igual sirve para editar, pero las instrucciones de
abajo son para VS Code, que es el estándar para Python.

1. Verifica que tengas Python instalado: abre una terminal (`cmd` o
   PowerShell en Windows, Terminal en Mac) y escribe:
   ```
   python --version
   ```
   Si da error, instala Python desde python.org (marca la casilla
   "Add Python to PATH" durante la instalación).
2. En VS Code, ve a la pestaña de Extensiones (ícono de cuadrados a la
   izquierda) e instala la extensión **Python** (de Microsoft).

## 2. Abrir el proyecto en VS Code

1. Descomprime la carpeta `proyecto_instrumentos` en un lugar fácil de
   encontrar (ej. Escritorio o Documentos).
2. En VS Code: `Archivo → Abrir carpeta...` y selecciona
   `proyecto_instrumentos` (la carpeta completa, no un archivo suelto).
3. Abre una terminal integrada: `Terminal → Nueva terminal`. Debe abrir
   ya posicionada dentro de `proyecto_instrumentos`.

## 3. Crear un entorno virtual e instalar librerías

Esto evita ensuciar tu instalación general de Python. En la terminal
que abriste dentro de VS Code:

```bash
python -m venv venv
```

Luego actívalo:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

Deberías ver `(venv)` al inicio de la línea de la terminal. Con eso
activado, instala las librerías:

```bash
pip install -r requirements.txt
```

(VS Code puede preguntarte "¿quieres usar este entorno como intérprete
del proyecto?" — dile que sí / "Select interpreter" y elige el que
tiene `venv` en la ruta.)

## 4. Qué va a pasar al correr cada paso (con tus 3 instrumentos)

Todo se ejecuta **desde la carpeta raíz** `proyecto_instrumentos/`
(no entres a `codigo/`), así:

**Paso 1 — Grabar.** Toca la misma nota (ej. La en la escala media) en
cada instrumento, dos veces cada uno:

```bash
python codigo/grabar_audio.py referencias/piano_1.wav
python codigo/grabar_audio.py referencias/piano_2.wav
python codigo/grabar_audio.py referencias/guitarra_1.wav
python codigo/grabar_audio.py referencias/guitarra_2.wav
python codigo/grabar_audio.py referencias/flauta_1.wav
python codigo/grabar_audio.py referencias/flauta_2.wav
```
Qué pasa: la terminal dice "Grabando 2.0 s... toca la nota ahora" y se
queda esperando 2 segundos grabando con tu micrófono; al terminar
guarda el archivo `.wav` dentro de `referencias/`. No abre ninguna
ventana, todo pasa en la terminal.

**Paso 2 — Ver el espectro (opcional pero recomendado).**
```bash
python codigo/analizar_espectro.py referencias/piano_1.wav
```
Qué pasa: se abre una ventana con una gráfica (usa `matplotlib`). Verás
un pico alto (la fundamental) y picos más chicos a la derecha
(armónicos). Cierra la ventana para que la terminal quede libre de
nuevo. Repite con `guitarra_1.wav` y `flauta_1.wav` y compara las tres
formas — ahí vas a *ver* por qué se pueden distinguir.

**Paso 3 — Ver los números extraídos (opcional, para entender).**
```bash
python codigo/extraer_caracteristicas.py referencias/piano_1.wav
```
Qué pasa: imprime en la terminal un resumen tipo:
```
f0: 440.3
armonicos: [1.0, 0.42, 0.18, ...]
centroide: 1523.7
energia_total: 8.9
```
Sin ventanas, solo texto.

**Paso 5 — El reconocimiento completo (el que de verdad importa).**
```bash
python codigo/main_reconocimiento.py
```
Qué pasa, en orden:
1. Como es la primera vez, no existe `banco_referencia.json`, así que
   el programa lee tus 6 archivos de `referencias/` (2 por
   instrumento), calcula sus características y guarda el promedio de
   cada instrumento en ese archivo. Verás en pantalla:
   `Banco de referencia listo: ['piano', 'guitarra', 'flauta']`
2. Inmediatamente pide grabar una muestra nueva ("toca la nota ahora")
   — toca cualquiera de los tres instrumentos.
3. Compara esa grabación contra el banco y al final imprime, por
   ejemplo: `Instrumento reconocido: guitarra`.

Para volver a probar con otro instrumento, corre
`python codigo/main_reconocimiento.py` otra vez (como
`banco_referencia.json` ya existe, esta vez se salta directo a grabar
la muestra nueva).

## 5. Cosas que probablemente fallen la primera vez (y cómo arreglarlas)

- **`sounddevice` no encuentra micrófono / da error de dispositivo**:
  revisa en Windows que el micrófono tenga permisos de acceso para
  aplicaciones de escritorio (Configuración → Privacidad → Micrófono).
- **`ModuleNotFoundError: No module named 'librosa'` (o cualquier otra)**:
  significa que el entorno virtual no está activado, o instalaste las
  librerías fuera de él. Verifica que la terminal muestre `(venv)` y
  vuelve a correr `pip install -r requirements.txt`.
- **El reconocimiento se equivoca mucho**: normal al principio — prueba
  grabando más cerca del instrumento, con menos ruido de fondo, y
  usando siempre la misma nota para el banco de referencia.

Cuando esto ya corra bien en tu computador con tus tres instrumentos,
seguimos con el paso de subirlo a GitHub.
