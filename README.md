# Reconocimiento de instrumentos con análisis espectral

Trabajo del curso de Teoría de Señales. Es un programa en Python que escucha una nota por el micrófono del computador y dice si suena a piano, guitarra, flauta o voz. Para decidirlo mira el espectro del sonido (la FFT): cada instrumento reparte su energía de forma distinta entre la frecuencia fundamental y los armónicos, y esa forma es lo que se compara.

Esta es la Etapa 1, con el micrófono del PC. La Etapa 2 pasará a Arduino/ESP32 y un dispositivo de medición más avanzado.

 ## Cómo funciona

1. Se graba un fragmento de 2 segundos.
2. Se calcula la FFT y se sacan unas pocas características: frecuencia fundamental, energía de los primeros 6 armónicos y centroide espectral.
3. Esos números se comparan con un banco de referencia (el promedio de las grabaciones de cada instrumento) y gana el más cercano.

## Carpetas

```
proyecto_instrumentos/
├── codigo/
│   ├── grabar_audio.py
│   ├── analizar_espectro.py
│   ├── extraer_caracteristicas.py
│   ├── clasificador.py
│   ├── main_reconocimiento.py
│   └── interfaz.py
├── referencias/        grabaciones de referencia (.wav)
├── requirements.txt
└── README.md
```

## Instalación

Necesitas Python 3. Desde la carpeta del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

Todo se corre desde la carpeta raíz del proyecto.

Primero hay que grabar las referencias, dos por instrumento y siempre la misma nota (yo usé Re). La grabación empieza apenas presionas Enter, así que toca la nota justo ahí y déjala sonar.

```powershell
python codigo\grabar_audio.py referencias\piano_1.wav
python codigo\grabar_audio.py referencias\piano_2.wav
python codigo\grabar_audio.py referencias\guitarra_1.wav
python codigo\grabar_audio.py referencias\guitarra_2.wav
python codigo\grabar_audio.py referencias\flauta_1.wav
python codigo\grabar_audio.py referencias\flauta_2.wav
python codigo\grabar_audio.py referencias\voz_1.wav
python codigo\grabar_audio.py referencias\voz_2.wav
```

Si quieres ver cómo se ve el espectro de una grabación:

```powershell
python codigo\analizar_espectro.py referencias\piano_1.wav
```

Para reconocer un instrumento por la terminal:

```powershell
python codigo\main_reconocimiento.py
```

La primera vez arma el banco de referencia y lo guarda en `banco_referencia.json`. Si cambias o agregas grabaciones, borra ese archivo para que se recalcule.

### Interfaz

Hay una ventana sencilla, hecha con tkinter (viene con Python), que muestra el resultado en grande con un ícono en vez de dejarlo solo en la terminal:

```powershell
python codigo\interfaz.py
```

Presionas "Grabar y reconocer", tocas la nota y aparece el instrumento detectado. Usa el mismo banco y la misma lógica que `main_reconocimiento.py`.

## Resultados

Probé 16 veces cada instrumento, tocando la misma nota:

| Instrumento | Aciertos | Intentos | Acierto |
|---|---|---|---|
| Piano | 16 | 16 | 100 % |
| Guitarra | 14 | 16 | 87,5 % |
| Flauta | 16 | 16 | 100 % |
| Voz | 15 | 16 | 93,75 % |
| Total | 61 | 64 | 95,3 % |

## Limitaciones

- Funciona bien con la nota con la que se hizo el banco. Cuando canté otra nota, el programa la clasificó como piano.
- Son solo dos grabaciones de referencia por instrumento, así que el promedio es poco estable.
- Las pruebas se hicieron con un solo micrófono, en un solo lugar y con un solo intérprete por instrumento.

Para mejorarlo habría que ampliar el banco con más notas y más grabaciones por instrumento.
