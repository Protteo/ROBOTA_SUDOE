#%%---------------------Entrainement manuel-------------------------------------------
import serial
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import csv
import os

# -------- CONFIG --------
PORT_SERIE = 'COM3'  # adapte ici
BAUDRATE = 9600
NOM_FICHIER_CSV = "donnees_manche.csv"

def charger_donnees_csv(nom_fichier):
    donnees = []
    labels = []
    if os.path.exists(nom_fichier):
        with open(nom_fichier, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 7:
                    continue
                try:
                    capteurs = list(map(float, row[:6]))
                    label = int(row[6])
                    donnees.append(capteurs)
                    labels.append(label)
                except:
                    continue
    return donnees, labels

def sauvegarder_donnees_csv(nom_fichier, donnees, labels):
    with open(nom_fichier, 'w', newline='') as f:
        writer = csv.writer(f)
        for capteurs, label in zip(donnees, labels):
            writer.writerow(capteurs + [label])

def collecte_donnees(port, baudrate, donnees_existantes, labels_existants):
    ser = serial.Serial(port, baudrate)
    print("Port série ouvert. Ctrl+C pour arrêter la collecte.")
    donnees = donnees_existantes.copy()
    labels = labels_existants.copy()

    # On ouvre en mode ajout pour sauvegarder les nouvelles données au fur et à mesure
    f_csv = open(NOM_FICHIER_CSV, 'a', newline='')
    writer = csv.writer(f_csv)

    try:
        while True:
            ligne = ser.readline().decode(errors='ignore').strip()
            valeurs = ligne.split(",")
            if len(valeurs) == 6:
                try:
                    capteurs = list(map(float, valeurs))
                except:
                    print("Erreur de conversion :", valeurs)
                    continue
                print(f"Capteurs reçus : {capteurs}")
                pos = input("Position (0 ou 1) ? ")
                if pos not in ['0', '1']:
                    print("Position invalide, réessaie.")
                    continue
                label = int(pos)
                donnees.append(capteurs)
                labels.append(label)
                writer.writerow(capteurs + [label])
                f_csv.flush()
    except KeyboardInterrupt:
        print("\nCollecte terminée.")
    ser.close()
    f_csv.close()
    return donnees, labels

def entrainer_modele(donnees, labels):
    from collections import Counter
    print(f"Nombre total d'exemples : {len(labels)}")
    print(f"Répartition des classes : {Counter(labels)}")

    X = np.array(donnees)
    y = np.array(labels)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = MLPClassifier(hidden_layer_sizes=(16,16), activation='relu', max_iter=1000)
    print("Entraînement du modèle...")
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"Précision sur le test : {score*100:.2f}%")

    joblib.dump(model, "mlp_manche_model.joblib")
    joblib.dump(scaler, "mlp_manche_scaler.joblib")
    print("Modèle et scaler sauvegardés.")

    return model, scaler

def prediction_realtime(port, baudrate):
    clf = joblib.load("mlp_manche_model.joblib")
    sc = joblib.load("mlp_manche_scaler.joblib")

    ser = serial.Serial(port, baudrate)
    print("Mode prédiction en temps réel. Ctrl+C pour quitter.")

    try:
        while True:
            ligne = ser.readline().decode(errors='ignore').strip()
            valeurs = ligne.split(",")
            if len(valeurs) == 6:
                try:
                    capteurs = list(map(float, valeurs))
                except:
                    continue
                X_input = np.array(capteurs).reshape(1, -1)
                X_scaled = sc.transform(X_input)
                pred = clf.predict(X_scaled)
                print(f"Capteurs: {capteurs} --> Prédiction position: {pred[0]}")
    except KeyboardInterrupt:
        print("\nArrêt du mode prédiction.")
    ser.close()

if __name__ == "__main__":
    print("=== Gestion des données du manche ===")
    if os.path.exists(NOM_FICHIER_CSV):
        choix = input(f"Fichier '{NOM_FICHIER_CSV}' existe. Souhaites-tu le réinitialiser ? (o/n) : ")
        if choix.lower() == 'o':
            os.remove(NOM_FICHIER_CSV)
            print("Fichier supprimé. Nouvelle collecte commencera sur base vide.")

    donnees, labels = charger_donnees_csv(NOM_FICHIER_CSV)
    print(f"Données chargées : {len(labels)} exemples.")

    donnees, labels = collecte_donnees(PORT_SERIE, BAUDRATE, donnees, labels)

    model, scaler = entrainer_modele(donnees, labels)

    # prediction_realtime(PORT_SERIE, BAUDRATE)

#%%---------------------------Entrainement triple------------------------------
import serial
import pandas as pd
import time
import os
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

PORT_SERIE = 'COM4'
BAUDRATE = 9600
N_CAPTEURS = 6
CSV_FILENAME = "donnees_manche_souple.csv"
SCALER_FILENAME = "scaler_manche.pkl"
MODEL_FILENAME = "modele_manche.pkl"
TEMPS_ACQUISITION_PAR_POSITION = 60  # secondes


def initialiser_csv():
    if os.path.exists(CSV_FILENAME):
        choix = input("Souhaitez-vous réinitialiser le fichier CSV ? (o/n) : ").lower()
        if choix == 'o':
            os.remove(CSV_FILENAME)
            print("Fichier réinitialisé.")
        else:
            print("Les nouvelles données seront ajoutées au fichier existant.")
    else:
        print("Le fichier n'existe pas, il sera créé.")


def lire_donnees_serie(ser):
    try:
        ligne = ser.readline().decode('utf-8').strip()
        valeurs = ligne.split(',')
        if len(valeurs) == N_CAPTEURS:
            return [float(v) for v in valeurs]
    except Exception:
        pass
    return None


def acquisition_par_positions():
    try:
        ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
        print("Connexion série ouverte.")
        time.sleep(2)

        position = 0
        data_total = []

        print("\nDébut de l'acquisition pour la position 0.")
        print("Appuyez sur Entrée pour passer à la position suivante.")

        while position <= 2:
            print(f"\n➡ Acquisition pour la position {position}.")
            input("→ Appuyez sur Entrée pour commencer l'acquisition pour cette position.")
            
            try:
                duree = float(input(f"⏱️ Entrez la durée d'acquisition en secondes pour la position {position} : "))
            except ValueError:
                print("Entrée invalide. Utilisation de 60 secondes par défaut.")
                duree = 60

            start_time = time.time()
            while True:
                if ser.in_waiting:
                    donnees = lire_donnees_serie(ser)
                    if donnees:
                        donnees.append(position)
                        data_total.append(donnees)
                        print(f"Position {position} : {donnees[:-1]}")

                if time.time() - start_time > duree:
                    break

            position += 1

        ser.close()

        colonnes = [f"capteur_{i+1}" for i in range(N_CAPTEURS)] + ["classe"]
        df = pd.DataFrame(data_total, columns=colonnes)

        if os.path.exists(CSV_FILENAME):
            df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
        else:
            df.to_csv(CSV_FILENAME, index=False)

        print(f"\n📁 Données enregistrées dans {CSV_FILENAME}")

    except Exception as e:
        print(f"Erreur : {e}")


def entrainer_modele():
    if not os.path.exists(CSV_FILENAME):
        print("Aucune donnée d'entraînement trouvée.")
        return None, None

    df = pd.read_csv(CSV_FILENAME)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_FILENAME)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

    model = MLPClassifier(hidden_layer_sizes=(12, 12), max_iter=300)
    model.fit(X_train, y_train)
    print(f"Précision sur test : {model.score(X_test, y_test)*100:.2f}%")
    joblib.dump(model, MODEL_FILENAME)
    print("🧠 Modèle entraîné et sauvegardé.")
    return model, scaler


def prediction_temps_reel():
    if not os.path.exists(MODEL_FILENAME) or not os.path.exists(SCALER_FILENAME):
        model, scaler = entrainer_modele()
        if model is None:
            print("Impossible de lancer la prédiction sans modèle.")
            return
    else:
        model = joblib.load(MODEL_FILENAME)
        scaler = joblib.load(SCALER_FILENAME)

    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("🔮 Prédictions en temps réel. Appuyez sur Ctrl+C pour arrêter.\n")

    try:
        while True:
            if ser.in_waiting:
                donnees = lire_donnees_serie(ser)
                if donnees:
                    entree = scaler.transform([donnees])
                    pred = model.predict(entree)[0]
                    proba = np.max(model.predict_proba(entree)) * 100
                    print(f"Prédiction : position {pred} (confiance : {proba:.1f}%)")
    except KeyboardInterrupt:
        print("\n⛔ Arrêt des prédictions.")
        ser.close()


if __name__ == "__main__":
    mode = input("Choisissez le mode : (a)cquisition, (p)rédiction ou (e)ntraînement ? : ").lower()
    if mode == 'a':
        initialiser_csv()
        acquisition_par_positions()
    elif mode == 'p':
        prediction_temps_reel()
    elif mode == 'e':
        entrainer_modele()
    else:
        print("Mode inconnu.")

#%%---------------------Réseau pour manche souple------------------------------
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
import os
print("Répertoire courant :", os.getcwd())


PORT_SERIE = 'COM4'
BAUDRATE = 115200
N_CAPTEURS = 6
CSV_FILENAME = "donnees_manche_souple.csv"
SCALER_FILENAME = "scaler_manche.pkl"
MODEL_FILENAME = "modele_manche.pkl"


def initialiser_csv():
    if os.path.exists(CSV_FILENAME):
        choix = input("Souhaitez-vous réinitialiser le fichier CSV ? (o/n) : ").lower()
        if choix == 'o':
            os.remove(CSV_FILENAME)
            print("Fichier réinitialisé.")
        else:
            print("Les nouvelles données seront ajoutées au fichier existant.")
    else:
        print("Le fichier n'existe pas, il sera créé.")


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
        pass
    return None


def acquisition_par_positions():
    try:
        ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
        print("Connexion série ouverte.")
        time.sleep(2)

        position = 0
        data_total = []

        print("\nDébut de l'acquisition pour la position 0.")
        print("Appuyez sur Entrée pour passer à la position suivante.")

        while position <= 2:
            print(f"\n➡ Acquisition pour la position {position}.")
            input("→ Appuyez sur Entrée pour commencer l'acquisition pour cette position.")
            
            try:
                duree = float(input(f"⏱️ Entrez la durée d'acquisition en secondes pour la position {position} : "))
            except ValueError:
                print("Entrée invalide. Utilisation de 60 secondes par défaut.")
                duree = 60

            start_time = time.time()
            while True:
                if ser.in_waiting:
                    donnees = lire_donnees_serie(ser)
                    if donnees:
                        donnees.append(position)
                        data_total.append(donnees)
                        print(f"Position {position} : {donnees[:-1]}")

                if time.time() - start_time > duree:
                    break

            position += 1

        ser.close()

        colonnes = [f"capteur_{i+1}" for i in range(N_CAPTEURS)] + ["classe"]
        df = pd.DataFrame(data_total, columns=colonnes)

        if os.path.exists(CSV_FILENAME):
            df.to_csv(CSV_FILENAME, mode='a', index=False, header=False)
        else:
            df.to_csv(CSV_FILENAME, index=False)

        print(f"\n📁 Données enregistrées dans {CSV_FILENAME}")

    except Exception as e:
        print(f"Erreur : {e}")


def entrainer_modele():
    if not os.path.exists(CSV_FILENAME):
        print("Aucune donnée d'entraînement trouvée.")
        return None, None

    df = pd.read_csv(CSV_FILENAME)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_FILENAME)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

    model = MLPClassifier(hidden_layer_sizes=(12, 12), max_iter=300)
    model.fit(X_train, y_train)
    print(f"Précision sur test : {model.score(X_test, y_test)*100:.2f}%")
    joblib.dump(model, MODEL_FILENAME)
    print("🧠 Modèle entraîné et sauvegardé.")
    return model, scaler


def prediction_temps_reel():
    if not os.path.exists(MODEL_FILENAME) or not os.path.exists(SCALER_FILENAME):
        model, scaler = entrainer_modele()
        if model is None:
            print("Impossible de lancer la prédiction sans modèle.")
            return
    else:
        model = joblib.load(MODEL_FILENAME)
        scaler = joblib.load(SCALER_FILENAME)

    ser = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
    print("🔮 Prédictions en temps réel. Appuyez sur Ctrl+C pour arrêter.\n")

    try:
        while True:
            if ser.in_waiting:
                donnees = lire_donnees_serie(ser)
                if donnees and len(donnees) == N_CAPTEURS:
                    entree = scaler.transform([donnees])
                    pred = model.predict(entree)[0]
                    proba = np.max(model.predict_proba(entree)) * 100
                    print(f"Prédiction : position {pred} (confiance : {proba:.1f}%)")
    except KeyboardInterrupt:
        print("\n⛔ Arrêt des prédictions.")
        ser.close()


if __name__ == "__main__":
    mode = input("Choisissez le mode : (a)cquisition, (p)rédiction ou (e)ntraînement ? : ").lower()
    if mode == 'a':
        initialiser_csv()
        acquisition_par_positions()
    elif mode == 'p':
        prediction_temps_reel()
    elif mode == 'e':
        entrainer_modele()
    else:
        print("Mode inconnu.")



#%%---------------------Vérification des valeurs-------------------------------
import csv
from collections import Counter

NOM_FICHIER_CSV = "donnees_manche_souple.csv"

def compter_classes(nom_fichier):
    labels = []
    with open(nom_fichier, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 7:
                continue
            try:
                label = int(row[6])
                labels.append(label)
            except:
                continue
    compteur = Counter(labels)
    for classe, nb in compteur.items():
        print(f"Classe {classe} : {nb} exemples")

if __name__ == "__main__":
    compter_classes(NOM_FICHIER_CSV)
