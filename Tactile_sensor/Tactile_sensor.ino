const int capteurPins[6] = {A17, A16, A10, A11, A12, A13};
const float VREF = 3.3;
const int resolution = 4096;

// Réglage de la fréquence cible (en Hz)
const unsigned long freqCible = 100; // <-- MODIFIE ICI la fréquence que tu veux
const unsigned long periodeCible = 1000000 / freqCible; // µs

unsigned long lastSendTime = 0;
unsigned long lastFreqDisplayTime = 0;
unsigned long loopCount = 0;

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);
  lastSendTime = micros();
  lastFreqDisplayTime = millis();
}

void loop() {
  unsigned long currentMicros = micros();

  // Forcer respect de la fréquence cible
  if (currentMicros - lastSendTime >= periodeCible) {
    lastSendTime = currentMicros;

    // Acquisition et envoi des 6 capteurs
    for (int i = 0; i < 6; i++) {
      float valeurBrute = analogRead(capteurPins[i]);
      float capteur = -valeurBrute + 4096;
      Serial.print(capteur);
      if (i < 5) Serial.print(",");
    }
    Serial.println();

    loopCount++; // Compter une acquisition

    // Toutes les 1 seconde, afficher la fréquence réelle
    unsigned long currentMillis = millis();
    if (currentMillis - lastFreqDisplayTime >= 1000) {
      Serial.print("Frequence acquisition reelle : ");
      Serial.print(loopCount);
      Serial.println(" Hz");
      loopCount = 0;
      lastFreqDisplayTime = currentMillis;
    }
  }
}
