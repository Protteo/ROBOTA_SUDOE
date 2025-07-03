//Le code est bon
const int capteurPin = A17; // Broche analogique utilisée
const int capteurPin2 = A16;
const int capteurPin3 = A10;

const float VREF = 3.3;    // Tension de référence analogique (adapter à ton Teensy)
const int resolution = 1024; // Résolution ADC (10 bits sur Teensy 3.2 ; 12 bits possible)

void setup() {
  Serial.begin(9600);
  analogReadResolution(10); // Mettre à 12 si ton Teensy le permet : analogReadResolution(12);
}

void loop() {
  float valeurBrute = analogRead(capteurPin);
  float valeurBrute2 = analogRead(capteurPin2);
  float valeurBrute3 = analogRead(capteurPin3);


//  float tension = (valeurBrute / (float)(resolution - 1)) * VREF;
//  float tension2 = (valeurBrute2 / (float)(resolution - 1)) * VREF;

  Serial.print("Valeur brute : ");
  Serial.print(valeurBrute);
  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension, 3);
//  Serial.println(" V");

  Serial.print("Valeur brute 2 : ") ;
  Serial.print(valeurBrute2);
  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension2, 3);
//  Serial.println(" V");

  Serial.print("Valeur brute 3 : ") ;
  Serial.print(valeurBrute3);
  Serial.print("\t");

  float rapport = valeurBrute/valeurBrute2;
//  float somme = valeurBrute + valeurBrute2;
  Serial.print("Rapport :");
  Serial.print(rapport);
  Serial.print("\t");
//  Serial.print("Somme des deux valeurs brutes :");
//  Serial.println(somme);
  delay(200);
  if (1010 >  valeurBrute2)
  {
    Serial.println("Tu le tiens en poignard");
  }
  else
  {
    Serial.println("Tu le tiens en standard");
  }
  }
