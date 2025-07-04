//Le code est bon
const int capteurPin = A17; // Broche analogique utilisée
const int capteurPin2 = A16;
const int capteurPin3 = A10;
const int capteurPin4 = A11;


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
  float valeurBrute4 = analogRead(capteurPin4);

  float capteur1 = (10.0/3)*valeurBrute-3300;
  float capteur2 = (10.0/3)*valeurBrute2-3300;
  float capteur3 = (10.0/3)*valeurBrute3-3300;
  float capteur4 = (10.0/3)*valeurBrute4-3300;
  

//  float tension = (valeurBrute / (float)(resolution - 1)) * VREF;
//  float tension2 = (valeurBrute2 / (float)(resolution - 1)) * VREF;
//  Serial.print("Val brute 1 : ");
//  Serial.print(valeurBrute);
//  Serial.print("\t");

//  Serial.print("Val brute 2 : ");
//  Serial.print(valeurBrute2);
//  Serial.print("\t");
  
//  Serial.print("Val brute 3 : ");
//  Serial.print(valeurBrute3);
//  Serial.print("\t");

//  Serial.print("Val brute 4 : ");
//  Serial.print(valeurBrute4);
//  Serial.print("\t");


  Serial.print("Cpt1 : ");
  Serial.print(capteur1);
  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension, 3);
//  Serial.println(" V");

  Serial.print("Cpt2 : ") ;
  Serial.print(capteur2);
  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension2, 3);
//  Serial.println(" V");

  Serial.print("Cpt3 : ") ;
  Serial.print(capteur3);
  Serial.print("\t");

  Serial.print("Cpt4 : ");
  Serial.println(capteur4);

//  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension, 3);
//  Serial.println(" V");

//  float avant = (valeurBrute+valeurBrute2)/2;
//  float arriere = (valeurBrute4+valeurBrute3)/2;

  float somme_standard = capteur1 + capteur2;
  float somme_poignard = capteur2 + capteur3;
//  Serial.print("Avant :");
//  Serial.print(avant);
//  Serial.print("\t");
  
//  Serial.print("Arrière :");
//  Serial.print(arriere);
//  Serial.print("\t");
  Serial.print("Somme standard :");
  Serial.print(somme_standard);
  Serial.print("\t");
  Serial.print("Somme poignard :");
  Serial.println(somme_poignard);


  
  delay(200);
  if (somme_standard < somme_poignard)
  {
    Serial.println("Tu le tiens en standard");
  }
  else
  {
    Serial.println("Tu le tiens en poignard");
  }
  }
