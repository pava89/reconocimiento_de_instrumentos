/*
  ETAPA 2 - Prueba de un micrófono
  ----------------------------------------------------------------------
  Sirve para comprobar que un micrófono está bien conectado antes de
  grabar en serio. Lee el pin del micrófono durante 20 ms y manda al PC
  el valor mínimo, el máximo y el promedio de ese rato.

  Elige el micrófono con PIN_MIC:
    MAX9814 -> 4  (D4)     en silencio el promedio queda en ~1300-1500 (~1,25 V)
    MAX4466 -> 15 (D15)    en silencio el promedio queda en ~1800-1900 (~1,65 V)

  Cómo verlo: Arduino IDE -> Serial Monitor o Serial Plotter, a 115200.
    - En silencio: mínimo y máximo casi juntos alrededor del promedio.
    - Con un aplauso o una nota: "minimo" baja y "maximo" sube.
    - Si "maximo" toca 4095 o "minimo" toca 0, la señal se satura:
      aleja el instrumento del micrófono.
    - Si todo marca 0 o un número bajo fijo: el micrófono no recibe
      corriente o algún pin no está metido hasta el fondo de la protoboard.
*/

const int PIN_MIC = 4;       // 4 = MAX9814 (D4), 15 = MAX4466 (D15)
const int VENTANA_MS = 20;   // cada cuánto se manda un dato al PC

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);  // valores de 0 a 4095
}

void loop() {
  int minimo = 4095;
  int maximo = 0;
  long suma = 0;
  long n = 0;

  unsigned long inicio = millis();
  while (millis() - inicio < (unsigned long)VENTANA_MS) {
    int valor = analogRead(PIN_MIC);
    if (valor < minimo) minimo = valor;
    if (valor > maximo) maximo = valor;
    suma += valor;
    n++;
  }

  // Formato "nombre:valor" para que el Serial Plotter dibuje una línea por cada uno.
  // "techo" y "piso" son fijas, solo para que la escala de la gráfica no salte.
  Serial.print("minimo:");   Serial.print(minimo);
  Serial.print(",maximo:");  Serial.print(maximo);
  Serial.print(",promedio:"); Serial.print(suma / n);
  Serial.println(",techo:4095,piso:0");
}
