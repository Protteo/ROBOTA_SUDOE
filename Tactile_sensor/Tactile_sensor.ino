//Le code est bon
const int capteurPin = A17; // Broche analogique utilisée
const int capteurPin2 = A16;
const int capteurPin3 = A10;
const int capteurPin4 = A11;
const int capteurPin5 = A12;
const int capteurPin6 = A13;


const float VREF = 3.3;    // Tension de référence analogique (adapter à ton Teensy)
const int resolution = 1024; // Résolution ADC (10 bits sur Teensy 3.2 ; 12 bits possible)

void setup() {
  Serial.begin(9600);
  analogReadResolution(10); // Mettre à 12 si ton Teensy le permet : analogReadResolution(12);
}

void loop() {
  float valeurBrute1 = analogRead(capteurPin);
  float valeurBrute2 = analogRead(capteurPin2);
  float valeurBrute3 = analogRead(capteurPin3);
  float valeurBrute4 = analogRead(capteurPin4);
  float valeurBrute5 = analogRead(capteurPin5);
  float valeurBrute6 = analogRead(capteurPin6);

  float capteur1 = (-100.0/1020)*valeurBrute1+100;
  float capteur2 = (-100.0/1020)*valeurBrute2+100;
  float capteur3 = (-100.0/1020)*valeurBrute3+100;
  float capteur4 = (-100.0/1020)*valeurBrute4+100;
  float capteur5 = -(100.0/1020)*valeurBrute5+100;
  float capteur6 = (-100.0/1020)*valeurBrute6+100;
 
//  float droite = capteur2 + capteur4;
//  float gauche = capteur1 + capteur3;
//  float haut = capteur1 +capteur2;
//  float bas= capteur3+ capteur4;
//  float Tot= haut + bas ;

//--------Pour graphique----------------------------------
//  float x1 =  valeurBrute1 * sqrt(2)/2;
//  float x2 = -valeurBrute2 * sqrt(2)/2;
//  float x3 =  valeurBrute3* sqrt(2)/2;
//  float x4 = -valeurBrute4 * sqrt(2)/2;
//  float x_tot = x1 + x2 + x3 + x4;
//  float x_moy = x_tot/4.0;
//  float x_sum = abs(x1) + abs(x2) + abs(x3) + abs(x4); 
//  float x=x_tot/x_sum;
//  
//
//  float y1 = -valeurBrute1 * sqrt(2)/2;
//  float y2 = -valeurBrute2 * sqrt(2)/2;
//  float y3 =  valeurBrute3* sqrt(2)/2;
//  float y4 =  valeurBrute4 * sqrt(2)/2;
//  float y_tot = y1 + y2 + y3 + y4;
//  float y_moy = y_tot/4.0;
//  float y_sum = abs(y1) + abs(y2) + abs(y3) + abs(y4);
//  float y = y_tot/y_sum;
  
//--------------------------------------------------------------------------------
//  float tension = (valeurBrute / (float)(resolution - 1)) * VREF;
//  float tension2 = (valeurBrute2 / (float)(resolution - 1)) * VREF;
//  Serial.print("Val brute 1 : ");
//  Serial.println(valeurBrute);
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


//  Serial.print("Cpt1 : ");
  Serial.print(capteur1);
  Serial.print(",");
//  Serial.print("\tTension : ");
//  Serial.print(tension, 3);
//  Serial.println(" V");

//  Serial.print("Cpt2 : ") ;
  Serial.print(capteur2);
  Serial.print(",");
//  Serial.print("\tTension : ");
//  Serial.print(tension2, 3);
//  Serial.println(" V");

//  Serial.print("Cpt3 : ") ;
  Serial.print(capteur3);
  Serial.print(",");

//  Serial.print("Cpt4 : ");
  Serial.print(capteur4);
  Serial.print(",");

  Serial.print(capteur5);
  Serial.print(",");

  Serial.println(capteur6);

//-------------------------Donne les coordonnées-----------------------------
//  Serial.print("(");
//  Serial.print(x);
//  Serial.print(",");
//  Serial.println(y);
//  Serial.println(")");
//---------------------------------------------------------------------------

//  Serial.print("\t");
//  Serial.print("\tTension : ");
//  Serial.print(tension, 3);
//  Serial.println(" V");

//  float avant = (valeurBrute+valeurBrute2)/2;
//  float arriere = (valeurBrute4+valeurBrute3)/2;

//  float somme_standard = capteur1 + capteur2;
//  float somme_poignard = capteur2 + capteur3;
//  Serial.print("Avant :");
//  Serial.print(avant);
//  Serial.print("\t");
  
//  Serial.print("Arrière :");
//  Serial.print(arriere);
//  Serial.print("\t");
//  Serial.print("Somme standard :");
//  Serial.print(somme_standard);
//  Serial.print("\t");
//  Serial.print("Somme poignard :");
//  Serial.println(somme_poignard);
//  Serial.print("droite : ");
//  Serial.println(droite);
//  Serial.print("gauche : ");
//  Serial.println(gauche);
//  Serial.print("haut : ");
//  Serial.println(haut);
//  Serial.print("bas : ");
//  Serial.println(bas);
//  Serial.print("Tot : ");
//  Serial.println(Tot);

  
//  delay(200);
//  if (somme_standard > somme_poignard or abs(somme_standard-somme_poignard)<300)
//  {
//    Serial.println("Tu le tiens en poignard");
//  }
//  else
//  {
//    Serial.println("Tu le tiens en standard");
//  }
    delay(10);
  }
