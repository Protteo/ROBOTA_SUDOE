const int capteurPin = A0; // Broche analogique utilisée
const int capteurPin2 = A1;"
const float VREF = 3.3;    // Tension de référence analogique (adapter à ton Teensy)
const int resolution = 1024; // Résolution ADC (10 bits sur Teensy 3.2 ; 12 bits possible)

void setup() {
  Serial.begin(9600);
  analogReadResolution(10); // Mettre à 12 si ton Teensy le permet : analogReadResolution(12);
}

void loop() {
  int valeurBrute = analogRead(capteurPin);
  int valeurBrute2 = analogRead(capteurPin2);

  float tension = (valeurBrute / (float)(resolution - 1)) * VREF;
  float tension2 = (valeurBrute2 / (float)(resolution - 1)) * VREF;

  Serial.print("Valeur brute : ");
  Serial.print(valeurBrute);
  Serial.print("\tTension : ");
  Serial.print(tension, 3);
  Serial.println(" V");

  Serial.print("Valeur brute 2 : ");
  Serial.print(valeurBrute2);
  Serial.print("\tTension : ");
  Serial.print(tension2, 3);
  Serial.println(" V");

  delay(200);
}
