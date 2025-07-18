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
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import csv
import os
from collections import Counter

# ====== PARAMÈTRES ======
PORT_SERIE = 'COM3'  # adapte ton port
BAUDRATE = 9600
NOM_FICHIER_CSV = "donnees_manche.csv"
CLASSES = [0, 1, 2]

def charger_donnees_csv(nom_fichier):
    donnees, labels = [], []
    if os.path.exists(nom_fichier):
        with open(nom_fichier, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 7:
                    try:
                        capteurs = list(map(float, row[:6]))
                        label = int(row[6])
                        donnees.append(capteurs)
                        labels.append(label)
                    except:
                        continue
    return donnees, labels

def collecte_par_bloc(port, baudrate, donnees_existantes, labels_existants):
    ser = serial.Serial(port, baudrate)
    print("Port série ouvert.")

    donnees = donnees_existantes.copy()
    labels = labels_existants.copy()

    with open(NOM_FICHIER_CSV, 'a', newline='') as f_csv:
        writer = csv.writer(f_csv)

        for position in CLASSES:
            input(f"\n▶ Appuie sur [Entrée] pour commencer la collecte pour la position {position}...")
            print(f"➡ Collecte de la position {position}. Appuie sur [Entrée] pour passer à la suivante...")
            while True:
                if os.name == 'nt':
                    import msvcrt
                    if msvcrt.kbhit() and msvcrt.getwch() == '\r':
                        break
                else:
                    import sys, select
                    if select.select([sys.stdin], [], [], 0)[0]:
                        sys.stdin.readline()
                        break

                ligne = ser.readline().decode(errors='ignore').strip()
                valeurs = ligne.split(",")
                if len(valeurs) == 6:
                    try:
                        capteurs = list(map(float, valeurs))
                        donnees.append(capteurs)
                        labels.append(position)
                        writer.writerow(capteurs + [position])
                        f_csv.flush()
                        print(f"Capteurs : {capteurs} --> Position {position}")
                    except:
                        continue

    ser.close()
    print("✅ Collecte terminée.")
    return donnees, labels

def entrainer_modele(donnees, labels):
    print(f"\n📊 Données totales : {len(labels)}")
    print("Répartition par classe :", dict(Counter(labels)))

    X = np.array(donnees)
    y = np.array(labels)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

    model = MLPClassifier(hidden_layer_sizes=(32,32), activation='relu', max_iter=1000)
    print("🧠 Entraînement du modèle...")
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"✅ Précision sur le test : {score*100:.2f}%")

    joblib.dump(model, "mlp_manche_model.joblib")
    joblib.dump(scaler, "mlp_manche_scaler.joblib")
    print("📦 Modèle et scaler sauvegardés.")

def prediction_realtime(port, baudrate):
    clf = joblib.load("mlp_manche_model.joblib")
    sc = joblib.load("mlp_manche_scaler.joblib")

    ser = serial.Serial(port, baudrate)
    print("🟢 Mode prédiction en temps réel (Ctrl+C pour quitter)")

    try:
        while True:
            ligne = ser.readline().decode(errors='ignore').strip()
            valeurs = ligne.split(",")
            if len(valeurs) == 6:
                try:
                    capteurs = list(map(float, valeurs))
                    X_input = np.array(capteurs).reshape(1, -1)
                    X_scaled = sc.transform(X_input)
                    pred = clf.predict(X_scaled)
                    print(f"Capteurs : {capteurs} --> Prédiction : {pred[0]}")
                except:
                    continue
    except KeyboardInterrupt:
        print("\n🔴 Arrêt du mode prédiction.")
    ser.close()

# ========== LANCEMENT ==========
if __name__ == "__main__":
    print("=== Réseau de Neurones – 3 Positions ===")

    if os.path.exists(NOM_FICHIER_CSV):
        choix = input(f"Le fichier '{NOM_FICHIER_CSV}' existe. Réinitialiser ? (o/n) : ")
        if choix.lower() == 'o':
            os.remove(NOM_FICHIER_CSV)
            print("📁 Fichier réinitialisé.")

    donnees, labels = charger_donnees_csv(NOM_FICHIER_CSV)
    print(f"Données existantes chargées : {len(labels)} exemples")

    donnees, labels = collecte_par_bloc(PORT_SERIE, BAUDRATE, donnees, labels)

    entrainer_modele(donnees, labels)

    # Décommente la ligne ci-dessous si tu veux activer la prédiction en live :
    # prediction_realtime(PORT_SERIE, BAUDRATE)

#%%---------------------Vérification des valeurs-------------------------------
import csv
from collections import Counter

NOM_FICHIER_CSV = "donnees_manche.csv"

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
