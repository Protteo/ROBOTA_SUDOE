#%%--------------------Importer les library------------------------------------
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import matplotlib.cm as cm
from collections import deque
import numpy as np
import time
# matplotlib.use('Qt5Agg')  # ou 'TkAgg' selon ton système


#%%--------------------Ouvre le port série-------------------------------------
ser = serial.Serial("COM3",9600)

#%%--------------------Preparer la figure--------------------------------------
fig, ax = plt.subplots()
point, =ax.plot([], [], 'ro')
ax.set_xlim(-1,1)
ax.set_ylim(-1,1)
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
num_capteurs = 6  # Change selon ton nombre de capteurs
labels = [f"Capteur {i+1}" for i in range(num_capteurs)]
history_length = 500  # Longueur du buffer

# ------------------- Buffers circulaires -------------------
histories = [deque(maxlen=history_length) for _ in range(num_capteurs)]

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
            
            if len(histories[i]) > 1:
                min_val = min(histories[i])
                max_val = max(histories[i])
                text_labels[i].set_text(f"Min: {min_val:.0f}\nMax: {max_val:.0f}")
                text_labels[i].set_y(max_val + 20)  # Décalage vertical du texte
            else:
                text_labels[i].set_text("")
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
reset_ax = plt.axes([0.4, 0.05, 0.2, 0.075])  # [x, y, width, height]
reset_button = Button(reset_ax, 'Reset')
reset_button.on_clicked(reset)

#%%-------------------------Ports séries actifs avec description---------------
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for p in ports:
    print(f"{p.device}: {p.description}")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
