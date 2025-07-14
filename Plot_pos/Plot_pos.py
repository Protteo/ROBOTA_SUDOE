#%%--------------------Importer les library------------------------------------
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import matplotlib.cm as cm
from collections import deque, Counter
import numpy as np
import time
# matplotlib.use('Qt5Agg')  # ou 'TkAgg' selon ton système


#%%--------------------Ouvre le port série-------------------------------------
ser = serial.Serial("COM3",9600)

#%%--------------------Preparer la figure--------------------------------------
fig, ax = plt.subplots()
point, =ax.plot([], [], 'ro')
ax.set_xlim(-100,100)
ax.set_ylim(-100,100)
ax.set_xlabel("Latéral")
ax.set_ylabel("Vertical")
ax.grid(True)

def update(frame):
    ser.reset_input_buffer()
    line = ser.readline().decode().strip()

    try:
        x_str, y_str = line.split(",")
        x=float(x_str)
        y=float(y_str)
        point.set_data(x, y)
        #Condition pour définir la position
        if x>0:
            print("Tu le tiens en standard")
        else:
            print("Tu le tiens en poignard")
    except:
        pass
    return point,

ani = animation.FuncAnimation(fig, update, blit=True, interval=50)
plt.show()

#%%-----------------Histogramme------------------------------------------------
num_capteurs = 2  # Change selon ton nombre de capteurs
labels = [f"Capteur {i+1}" for i in range(num_capteurs)]

# history_length = 500  # Longueur du buffer

# ------------------- Buffers circulaires -------------------

histories = [[] for _ in range(num_capteurs)]

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Laisse de la place pour le bouton
bars = ax.bar(labels, [0]*num_capteurs, color='skyblue')
ax.set_ylim(0, 100)  # Plage max pour un capteur analogique 10 bits (Arduino)
text_labels = []


# Affichage initial des min/max
for i in range(num_capteurs):
    txt = ax.text(i, 0, "", ha='center', va='bottom', fontsize=9)
    text_labels.append(txt)

def update_hist(frame):
    ser.reset_input_buffer()
    line = ser.readline().decode().strip()
    try:
        valeurs_str = line.split(",")
        valeurs = list(map(float, valeurs_str))
        if len(valeurs) != num_capteurs:
            return bars
        max_global = 100  # Valeur max de base

        for i, (bar, val) in enumerate(zip(bars, valeurs)):
            bar.set_height(val)
            histories[i].append(val)
            
            # if len(histories[i]) > 1:
            #     min_val = min(histories[i])
            #     max_val = max(histories[i])
            #     text_labels[i].set_text(f"Min: {min_val:.0f}\nMax: {max_val:.0f}")
            #     text_labels[i].set_y(max_val + 20)  # Décalage vertical du texte
            # else:
            #     text_labels[i].set_text("")
        ax.set_ylim(0, max_global + 50)  # Ajuste la hauteur du graphe dynamiquement

    except Exception as e:
        print("Erreur :", e)
    return tuple(bars) + tuple(text_labels)


    
ani = animation.FuncAnimation(fig, update_hist, interval=50)
plt.ylabel("Valeur du capteur")
plt.title("Mesures en temps réel")
plt.grid(True, axis='y')
plt.tight_layout()
plt.show()

# ------------------- Fonction de reset
def reset(event):
    for i in range(num_capteurs):
        histories[i].clear()
        bars[i].set_height(0)
        text_labels[i].set_text("")
        text_labels[i].set_y(0)
    ax.set_ylim(0, 1050)
    print("Historiques réinitialisés.")
    
# ------------------- Ajout d'une touche 'r' pour reset
# reset_ax = plt.axes([0.4, 0.05, 0.2, 0.075])  # [x, y, width, height]
# reset_button = Button(reset_ax, 'Reset')
# reset_button.on_clicked(reset)

#%%-------------------------Ports séries actifs avec description---------------
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for p in ports:
    print(f"{p.device}: {p.description}")
    
#%%--------------------Acquisition avec diagramme couleurs---------------------
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import threading
import numpy as np
import time
from mpl_toolkits.mplot3d import Axes3D

# --------------------- CONFIGURATION ---------------------
mode = "fenetre"  # "continu" ou "fenetre"
interval_update_sec = 1  # fréquence de mise à jour histogramme (en secondes)
num_capteurs = 6
port_serial = "COM3"
baudrate = 9600
acquisition_active = True

# --------------------- INITIALISATION ---------------------
ser = serial.Serial(port_serial, baudrate, timeout=1)
def on_close(event):
    global fenetres_ouvertes, acquisition_active, thread_acq
    fenetres_ouvertes -= 1
    if fenetres_ouvertes == 0:
        print("Toutes les fenêtres sont fermées. Fermeture du port série...")
        acquisition_active = False
        if thread_acq is not None:
            thread_acq.join(timeout=2)  # Attend la fin du thread (max 2s)
        try:
            ser.close()
            print("Port série fermé proprement.")
        except:
            print("Erreur lors de la fermeture du port série.")


labels = [f"Capteur {i+1}" for i in range(num_capteurs)]
data_buffers = [deque() for _ in range(num_capteurs)]      # Historique complet
data_fenetre = [deque() for _ in range(num_capteurs)]      # Fenêtre glissante 5s
valeurs_en_temps_reel = [0.0 for _ in range(num_capteurs)] # Dernières valeurs
# Nouveau : pour gérer la fermeture propre des deux fenêtres
fenetres_ouvertes = 3  # nombre total de fenêtres à gérer


lock = threading.Lock()

# --------------------- THREAD DE LECTURE SERIE ---------------------
def lire_serial():
    global acquisition_active
    while acquisition_active:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            valeurs = list(map(float, line.split(",")))
            if len(valeurs) != num_capteurs:
                continue
            now = time.time()
            with lock:
                for i in range(num_capteurs):
                    val = valeurs[i]
                    valeurs_en_temps_reel[i] = val
                    data_buffers[i].append(val)
                    data_fenetre[i].append((now, val))
        except Exception:
            continue

thread_acq = threading.Thread(target=lire_serial, daemon=True)
thread_acq.start()

# Petit délai pour laisser l'acquisition série démarrer
# time.sleep(1)

# --------------------- FENETRE 1 : HISTOGRAMMES ---------------------
fig_freq, axs_freq = plt.subplots(1, num_capteurs, figsize=(6 * num_capteurs, 4))
if num_capteurs == 1:
    axs_freq = [axs_freq]

def update_histogram(frame):
    with lock:
        now = time.time()
        snapshots = []
        for i in range(num_capteurs):
            if mode == "fenetre":
                while data_fenetre[i] and now - data_fenetre[i][0][0] > 5:
                    data_fenetre[i].popleft()
                valeurs = [v for (t, v) in data_fenetre[i]]
            else:
                valeurs = list(data_buffers[i])
            snapshots.append(valeurs)

    for i in range(num_capteurs):
        ax = axs_freq[i]
        ax.clear()
        ax.set_title(f"Capteur {i+1} – Mode: {mode}")
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 50)
        ax.set_xlabel("Valeur")
        ax.set_ylabel("Fréquence")

        valeurs = snapshots[i]
        if valeurs:
            counts, bins = np.histogram(valeurs, bins=30, range=(0, 100))
            colors = plt.cm.jet(counts / counts.max()) if counts.max() > 0 else 'gray'
            ax.bar(bins[:-1], counts, width=(bins[1] - bins[0]), color=colors, align='edge')
        else:
            ax.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', transform=ax.transAxes)

ani_freq = animation.FuncAnimation(fig_freq, update_histogram, interval=interval_update_sec * 1000)

# --------------------- FENETRE 2 : TEMPS REEL ---------------------
fig_rt, ax_rt = plt.subplots()
bars = ax_rt.bar(labels, [0] * num_capteurs, color='skyblue')
ax_rt.set_ylim(0, 100)
ax_rt.set_title("Valeurs en temps réel")
ax_rt.set_ylabel("Valeur")
text_labels = [ax_rt.text(i, 0, "", ha='center', va='bottom') for i in range(num_capteurs)]

def update_realtime(frame):
    with lock:
        snapshot = list(valeurs_en_temps_reel)
    for i, bar in enumerate(bars):
        val = snapshot[i]
        bar.set_height(val)
        text_labels[i].set_text(f"{val:.1f}")
        text_labels[i].set_y(val + 2)

ani_rt = animation.FuncAnimation(fig_rt, update_realtime, interval=200)

#----------------------Ferme le port série proprement
# Attache cette fonction aux deux fenêtres
fig_freq.canvas.mpl_connect("close_event", on_close)
fig_rt.canvas.mpl_connect("close_event", on_close)

# --------------------- FENETRE 3 : 3D MANCHE + CENTRE DES FORCES
fig_3d = plt.figure()
ax_3d = fig_3d.add_subplot(111, projection='3d')
fig_3d.canvas.mpl_connect("close_event", on_close)

# Coordonnées fixes des capteurs [x, y, z] en cm
capteurs_coords = np.array([
    [2, -1.5, 0.5],  # Capteur 1
    [2, +1.5, 0.5],  # Capteur 2
    [8, -1.5, 0.5],  # Capteur 3
    [8, +1.5, 0.5],  # Capteur 4
    [5, 0.0, 2.0],   # Capteur 5
    [2, 0.0, 2.0],   # Capteur 6
])

# Manche dimensions (pour affichage)
manche_length = 10
manche_width = 3
manche_height = 2

# Boîte du manche pour visuel
def draw_manche(ax):
    # Crée les coins d'une boîte
    from itertools import product, combinations
    r = [0, manche_length]
    w = [-manche_width/2, manche_width/2]
    h = [0, manche_height]
    points = list(product(r, w, h))
    for s, e in combinations(points, 2):
        if sum([s[i] != e[i] for i in range(3)]) == 1:
            ax.plot3D(*zip(s, e), color="gray", alpha=0.4)

def update_3d(frame):
    with lock:
        forces = np.array(valeurs_en_temps_reel)
    
    ax_3d.clear()
    draw_manche(ax_3d)
    
    ax_3d.set_xlim(0, manche_length)
    ax_3d.set_ylim(-manche_width/2 - 1, manche_width/2 + 1)
    ax_3d.set_zlim(0, manche_height + 1)
    ax_3d.set_title("Manche + Centre des forces")
    ax_3d.set_xlabel("X (longueur)")
    ax_3d.set_ylabel("Y (largeur)")
    ax_3d.set_zlabel("Z (hauteur)")

    # Affiche capteurs
    for i, (x, y, z) in enumerate(capteurs_coords):
        ax_3d.scatter(x, y, z, color='blue')
        ax_3d.text(x, y, z + 0.2, f"{i+1}", color='blue')
    # Calcul du centre de force
    if np.sum(forces) > 0:
        center_force = np.average(capteurs_coords, axis=0, weights=forces)
        ax_3d.scatter(*center_force, color='red', s=100, label='Centre des forces')
        ax_3d.legend()

ani_3d = animation.FuncAnimation(fig_3d, update_3d, interval=200)


# --------------------- AFFICHAGE FINAL 
plt.show()









    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
