import serial
import pandas as pd
import time
import os
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import re

# === Paramètres à personnaliser ===
DOSSIER_TRAVAIL = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\Capteurs_tactiles\PPorPS"
PORT_SERIE = 'COM4'
BAUDRATE = 115200
N_CAPTEURS = 6
NB_VALEURS_GLISSANTES = 1  # Valeurs par capteur (fenêtre)
HIDDEN_LAYER = (4)
ACTIVATION = "relu" # "logistic" ou "tanh" ou "identity" ou "relu"
ALPHA = 0.0001 #Régularisation L2
MAX_ITER = 2500
CLASSES = [
    # "neutre",
    # "rectiligne_std",
    # "courbe_droite_std",
    # "courbe_gauche_std",
    # "rectiligne_poignard",
    # "courbe_gauche_poignard",
    # "courbe_droite_poignard"
    "Standard",
    "Poignard"
]

CSV_FILENAME = os.path.join(DOSSIER_TRAVAIL, "donnees_manche_souple.csv")
SCALER_FILENAME = os.path.join(DOSSIER_TRAVAIL, "scaler.pkl")
MODEL_FILENAME = os.path.join(DOSSIER_TRAVAIL, "modele.pkl")

# === Fonctions ===
def lire_donnees_serie(ser):
    try:
        ligne = ser.readline().decode('utf-8').strip()
        matches = re.findall(r'R(\d):(\d+)', ligne)
        values = [0] * N_CAPTEURS
        for sensor, val in matches:
            idx = int(sensor) - 1
            if 0 <= idx < N_CAPTEURS:
                values[idx] = int(val)
        return values
    except Exception:
        return None

def initialiser_csv():
    if os.path.exists(CSV_FILENAME):
        choix = input("Réinitialiser le fichier CSV ? (o/n) : ").lower()
        if choix == 'o':
            os.remove(CSV_FILENAME)
            print("Fichier CSV réinitialisé.")
        else:
            print("Les nouvelles données seront ajoutées.")
    else:
        print("Le fichier sera créé.")

def acquisition_par_classe():
    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("Connexion série établie.")
    time.sleep(2)

    data_total = []

    for classe in CLASSES:
        input(f"\nPréparez la classe '{classe}'. Appuyez sur Entrée pour démarrer l'acquisition.")
        try:
            duree = float(input("Durée d'acquisition (sec) : "))
        except ValueError:
            duree = 60
            print("Durée par défaut : 60s.")

        buffer = []
        start = time.time()
        while time.time() - start < duree:
            if ser.in_waiting:
                donnees = lire_donnees_serie(ser)
                if donnees:
                    buffer.append(donnees)
                    if len(buffer) >= NB_VALEURS_GLISSANTES:
                        # Prendre les dernières N valeurs
                        fenetre = buffer[-NB_VALEURS_GLISSANTES:]
                        ligne = sum(fenetre, [])  # Aplatir
                        ligne.append(classe)
                        data_total.append(ligne)
                        print(f"{classe} : {ligne[:-1]}")

        print(f"Acquisition terminée pour {classe}.")

    ser.close()
    colonnes = [f"capteur_{i+1}_t{j+1}" for j in range(NB_VALEURS_GLISSANTES) for i in range(N_CAPTEURS)] + ["classe"]
    df = pd.DataFrame(data_total, columns=colonnes)

    if os.path.exists(CSV_FILENAME):
        df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
    else:
        df.to_csv(CSV_FILENAME, index=False)

    print(f"✅ Données enregistrées dans {CSV_FILENAME}")

def entrainer_modele(HIDDEN_LAYER, MAX_ITER): #Permet de régler les paramètres du réseau de neurones
    if not os.path.exists(CSV_FILENAME):
        print("Fichier CSV non trouvé.")
        return

    df = pd.read_csv(CSV_FILENAME)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_FILENAME)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

    model = MLPClassifier(hidden_layer_sizes=HIDDEN_LAYER, max_iter=MAX_ITER, solver='adam', activation='logistic', alpha=ALPHA, verbose=True)
    model.fit(X_train, y_train)

    print(f"🎯 Précision : {model.score(X_test, y_test)*100:.2f}%")
    joblib.dump(model, MODEL_FILENAME)
    print("🧠 Modèle sauvegardé.")

def prediction_temps_reel():
    if not os.path.exists(MODEL_FILENAME) or not os.path.exists(SCALER_FILENAME):
        print("Modèle non trouvé.")
        return

    model = joblib.load(MODEL_FILENAME)
    scaler = joblib.load(SCALER_FILENAME)
    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("🔮 Prédictions en cours. Ctrl+C pour arrêter.")

    buffer = []

    try:
        while True:
            if ser.in_waiting:
                donnees = lire_donnees_serie(ser)
                if donnees:
                    buffer.append(donnees)
                    if len(buffer) >= NB_VALEURS_GLISSANTES:
                        fenetre = buffer[-NB_VALEURS_GLISSANTES:]
                        entree = sum(fenetre, [])
                        X_input = scaler.transform([entree])
                        pred = model.predict(X_input)[0]
                        proba = np.max(model.predict_proba(X_input)) * 100
                        print(f"Prédiction : {pred} ({proba:.1f}%)")
    except KeyboardInterrupt:
        print("⛔ Arrêt.")
        ser.close()

# === Menu principal ===
if __name__ == "__main__":
    mode = input("Mode : (a)cquisition, (e)ntrainement, (p)rédiction ? ").lower()
    if mode == 'a':
        initialiser_csv()
        acquisition_par_classe()
    elif mode == 'e':
        entrainer_modele(HIDDEN_LAYER, MAX_ITER)
    elif mode == 'p':
        prediction_temps_reel()
    else:
        print("Mode inconnu.")

