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

"""This code works with the flexible handle.
It creates csv files in which are stored the data of several acquisitions made by the user about the way of holding the knife.
First the user has to hold the knife through several positions, then he has to train the neural network and finally, he can start to predict new positions.
You have to launch this code three times to do those three steps."""


# === Paramètres à personnaliser ===
DOSSIER_TRAVAIL = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\PPorPS"
PORT_SERIE = 'COM4'
BAUDRATE = 115200
N_CAPTEURS = 6
NB_VALEURS_GLISSANTES = 1  # Valeurs par capteur (fenêtre)
HIDDEN_LAYER = (4)
ACTIVATION = "relu" # "logistic" or "tanh" or "identity" or "relu"
ALPHA = 0.0001 #Régularisation L2
MAX_ITER = 2500
CLASSES = [
    # "neutral",
    # "straight_std",
    # "curve_right_std",
    # "curve_left_std",
    # "straight_reverse",
    # "curve_left_reverse",
    # "curve_right_reverse"
    "Standard",
    "Reverse"
]

CSV_FILENAME = os.path.join(DOSSIER_TRAVAIL, "donnees_manche_souple.csv") #Name of the csv file
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
        choix = input("Reset the csv file ? (y/n) : ").lower()
        if choix == 'y':
            os.remove(CSV_FILENAME)
            print("csv file reset")
        else:
            print("New data will be added")
    else:
        print("The file will be set")

def acquisition_par_classe():
    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("Link with the serial port : ok")
    time.sleep(2)

    data_total = []

    for classe in CLASSES:
        input(f"\nPrepare the classe '{classe}'. Press Enter to start getting data.")
        try:
            duree = float(input("Getting time (sec) : "))
        except ValueError:
            duree = 60
            print("Default time : 60s.")

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

        print(f"Getting over for {classe}.")

    ser.close()
    colonnes = [f"capteur_{i+1}_t{j+1}" for j in range(NB_VALEURS_GLISSANTES) for i in range(N_CAPTEURS)] + ["classe"]
    df = pd.DataFrame(data_total, columns=colonnes)

    if os.path.exists(CSV_FILENAME):
        df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
    else:
        df.to_csv(CSV_FILENAME, index=False)

    print(f"✅ Data saved in {CSV_FILENAME}")

def entrainer_modele(HIDDEN_LAYER, MAX_ITER): #Permet de régler les paramètres du réseau de neurones
    if not os.path.exists(CSV_FILENAME):
        print("CSV file not found.")
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

    print(f"🎯 Accuracy : {model.score(X_test, y_test)*100:.2f}%")
    joblib.dump(model, MODEL_FILENAME)
    print("🧠 Model saved")

def prediction_temps_reel():
    if not os.path.exists(MODEL_FILENAME) or not os.path.exists(SCALER_FILENAME):
        print("Model not found")
        return

    model = joblib.load(MODEL_FILENAME)
    scaler = joblib.load(SCALER_FILENAME)
    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("🔮 Prédictions ongoing. Ctrl+C to stop.")

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
        print("⛔ Stop.")
        ser.close()

# === Menu principal ===
if __name__ == "__main__":
    mode = input("Mode : (a)cquisition, (t)raining, (p)rédiction ? ").lower()
    if mode == 'a':
        initialiser_csv()
        acquisition_par_classe()
    elif mode == 't':
        entrainer_modele(HIDDEN_LAYER, MAX_ITER)
    elif mode == 'p':
        prediction_temps_reel()
    else:
        print("Mode inconnu.")

