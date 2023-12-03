#define USE_ARDUINO_INTERRUPTS true    // Set-up low-level interrupts for most accurate BPM math.
#include <PulseSensorPlayground.h>     // Incluye la biblioteca PulseSensorPlayground.
#include <SoftwareSerial.h>           // Incluye la biblioteca SoftwareSerial.

// Variables del sensor de pulso
const int PulseWire = 0;            // Sensor de pulso conectado al PIN ANALÓGICO 0
const int LED = LED_BUILTIN;         // LED incorporado de Arduino cerca del PIN 13.
int Threshold = 550;                 // Umbral para contar un latido.

PulseSensorPlayground pulseSensor;  // Crea una instancia del objeto PulseSensorPlayground llamada "pulseSensor"

// Variables para el módulo Bluetooth
SoftwareSerial BT(10, 11);  // Pines RX y TX para la comunicación Bluetooth

void setup() {
  Serial.begin(9600);  // Inicializa la comunicación serial para el Monitor Serie.
  BT.begin(9600);      // Inicializa la comunicación serial para el módulo Bluetooth.

  // Configura el objeto PulseSensor asignando nuestras variables.
  pulseSensor.analogInput(PulseWire);
  pulseSensor.blinkOnPulse(LED);
  pulseSensor.setThreshold(Threshold);

  if (pulseSensor.begin()) {
    Serial.println("Se creó un objeto pulseSensor.");
  }
}

void loop() {
  if (pulseSensor.sawStartOfBeat()) {
    int myBPM = pulseSensor.getBeatsPerMinute();
    Serial.println("♥ Un latido ha ocurrido.");
    Serial.print("BPM: ");
    Serial.println(myBPM);

    // Envía los datos de BPM al dispositivo emparejado a través del módulo Bluetooth
    BT.println(myBPM);
  }

  delay(20);
}
