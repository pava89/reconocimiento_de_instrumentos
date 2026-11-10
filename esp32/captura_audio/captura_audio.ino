/*
  ETAPA 2 - Captura de audio con ESP32 + dos micrófonos (MAX9814 y MAX4466)
  ----------------------------------------------------------------------
  Cada micrófono convierte el sonido en voltaje (una onda centrada en un
  voltaje fijo: ~1,25 V el MAX9814 y ~1,65 V el MAX4466). El ESP32 mide
  ese voltaje con su ADC de 12 bits (números de 0 a 4095) FS veces por
  segundo durante 2 segundos, guarda las muestras en su memoria y después
  las manda al PC por el cable USB.

  Los dos micrófonos quedan conectados a la vez, cada uno en su pin, y el
  PC decide con cuál grabar. El ESP32 no analiza nada: la FFT, las
  características y la clasificación las hace Python (codigo/grabar_esp32.py).

  ESPECIFICACIONES DEL MUESTREO
    - Frecuencia de muestreo (FS) ....... 16000 Hz (una muestra cada 62,5 us)
    - Frecuencia máxima que se ve ....... 8000 Hz (Nyquist = FS / 2)
    - Duración de cada grabación ........ 2 s  ->  N = 32000 muestras
    - Resolución del ADC ................ 12 bits (0 a 4095)
    - Tiempo medido por lectura ......... ~40 us (cabe dentro de los 62,5 us)
    - Envío al PC ....................... binario, 2 bytes por muestra, 921600 baudios

  Cómo se entienden el PC y el ESP32:
    PC manda 'P' -> ESP32 contesta "PONG"        (comprobar que está vivo)
    PC manda 'A' -> graba con el MAX9814 (pin D4)
    PC manda 'B' -> graba con el MAX4466 (pin D15)
    ('R' también graba con el MAX9814, por compatibilidad)
    Al grabar, el ESP32 contesta "GRABANDO", graba 2 s y luego manda:
                    "DATOS <n> <fs_real> <atrasos>"
                    <n muestras de 2 bytes cada una, en binario>
                    "FIN"

  Conexión (ver README):
    3V3 del ESP32 -> línea roja (+)     GND del ESP32 -> línea verde (-)
    MAX9814: Vdd y Gain -> +, GND -> -, Out -> D4, AR sin conectar
    MAX4466: VCC -> +, GND -> -, OUT -> D15

  Importante: cierra el Monitor Serie y el Serial Plotter del Arduino IDE
  antes de correr el programa de Python; si no, el puerto queda ocupado.
*/

#include "esp_timer.h"

const int PIN_MAX9814 = 4;                     // Out del MAX9814 (pin D4)
const int PIN_MAX4466 = 15;                    // OUT del MAX4466 (pin D15)
const int PIN_LED = 2;                         // LED azul de la placa: prendido mientras graba
const uint32_t FS = 16000;                     // muestras por segundo -> se ve hasta 8000 Hz (Nyquist)
const uint32_t DURACION_MS = 2000;             // igual que en la Etapa 1
const uint32_t N = FS * DURACION_MS / 1000;    // 32000 muestras
const uint32_t BAUDIOS = 921600;               // debe ser igual a BAUDIOS en codigo/grabar_esp32.py

static uint16_t muestras[N];                   // 32000 x 2 bytes = 64 KB de RAM

float fs_real = 0;      // frecuencia de muestreo que se logró de verdad
uint32_t atrasos = 0;   // muestras que se tomaron tarde (el ADC no alcanzó)

void grabar(int pin) {
  const int64_t periodo_us = 1000000LL / FS;   // 62 us entre muestra y muestra
  const int64_t inicio = esp_timer_get_time();
  int64_t ultima = inicio;
  atrasos = 0;

  for (uint32_t i = 0; i < N; i++) {
    // Momento exacto en que toca tomar la muestra i. Se calcula desde el
    // inicio para que los errores no se acumulen: el muestreo queda parejo,
    // que es lo que necesita la FFT.
    const int64_t objetivo = inicio + (int64_t)i * 1000000LL / FS;
    int64_t ahora;
    while ((ahora = esp_timer_get_time()) < objetivo) {
      // esperar
    }
    if (ahora - objetivo > periodo_us / 4) atrasos++;
    ultima = ahora;
    muestras[i] = analogRead(pin);
  }

  fs_real = (N - 1) * 1000000.0f / (float)(ultima - inicio);
}

void enviar() {
  Serial.print("DATOS ");
  Serial.print(N);
  Serial.print(" ");
  Serial.print(fs_real, 2);
  Serial.print(" ");
  Serial.println(atrasos);
  Serial.write((const uint8_t *)muestras, sizeof(muestras));
  Serial.println();
  Serial.println("FIN");
}

float medir_lectura_us(int pin) {
  const int64_t t0 = esp_timer_get_time();
  for (int i = 0; i < 1000; i++) analogRead(pin);
  return (esp_timer_get_time() - t0) / 1000.0f;
}

void setup() {
  Serial.begin(BAUDIOS);
  pinMode(PIN_LED, OUTPUT);
  analogReadResolution(12);

  Serial.print("ESP32 listo. FS = ");
  Serial.print(FS);
  Serial.print(" Hz. Cada lectura tarda ");
  Serial.print(medir_lectura_us(PIN_MAX9814), 1);
  Serial.print(" us en D4 y ");
  Serial.print(medir_lectura_us(PIN_MAX4466), 1);
  Serial.print(" us en D15 (limite: ");
  Serial.print(1000000.0f / FS, 1);
  Serial.println(" us).");
}

void loop() {
  if (!Serial.available()) return;
  const char orden = Serial.read();

  int pin = -1;
  if (orden == 'A' || orden == 'R') pin = PIN_MAX9814;
  else if (orden == 'B') pin = PIN_MAX4466;

  if (orden == 'P') {
    Serial.println("PONG");
  } else if (pin >= 0) {
    Serial.println("GRABANDO");
    Serial.flush();                 // que el aviso salga antes de empezar a medir
    digitalWrite(PIN_LED, HIGH);
    grabar(pin);
    digitalWrite(PIN_LED, LOW);
    enviar();
  }
  // Cualquier otro carácter (por ejemplo un Enter) se ignora.
}
