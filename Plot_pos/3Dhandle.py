import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib.colors import Normalize

# --- Paramètres de configuration (à ajuster) ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
STL_FILE_PATH = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\ROBOTA SUDOE 2025 BRIANCON-PROVERBIO\CAD\STL\Handle\Manche_couteau.STL"

rect_params = [
    {'x': 60, 'y': 33, 'z': 31, 'width': 60, 'height': 20, 'depth': 1, 'color': 'blue'},
    {'x': 60, 'y': 33, 'z': 7, 'width': 60, 'height': 20, 'depth': 1, 'color': 'blue'},
    {'x': 125, 'y': 33, 'z': 31, 'width': 60, 'height': 20, 'depth': 1, 'color': 'blue'},
    {'x': 125, 'y': 33, 'z': 7, 'width': 60, 'height': 20, 'depth': 1, 'color': 'blue'},
    {'x': 125, 'y': 45, 'z': 18.8, 'width': 60, 'height': 1, 'depth': 20, 'color': 'blue'},
    {'x': 60, 'y': 45, 'z': 18.8, 'width': 60, 'height': 1, 'depth': 20, 'color': 'blue'}
]

# --- Initialisation ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) 
    time.sleep(2)
    ser.reset_input_buffer() 
    print("Connexion au port série réussie et buffer vidé.")
except serial.SerialException as e:
    print(f"Erreur de connexion au port série {SERIAL_PORT}: {e}")
    exit()

print("Initialisation de la figure Matplotlib...")
try:
    your_mesh = mesh.Mesh.from_file(STL_FILE_PATH)
except FileNotFoundError:
    print(f"Erreur: Le fichier STL '{STL_FILE_PATH}' est introuvable.")
    exit()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.add_collection3d(mplot3d.art3d.Poly3DCollection(your_mesh.vectors, alpha=0.5))

norm = Normalize(vmin=0, vmax=1023)

rects = []
for params in rect_params:
    x, y, z = params['x'], params['y'], params['z']
    width, height, depth = params['width'], params['height'], params['depth']
    
    verts = [
        [x, y, z], [x + width, y, z], [x + width, y + height, z], [x, y + height, z],
        [x, y, z + depth], [x + width, y, z + depth], [x + width, y + height, z + depth], [x, y + height, z + depth]
    ]
    faces = [
        [verts[0], verts[1], verts[2], verts[3]], [verts[4], verts[5], verts[6], verts[7]], 
        [verts[0], verts[1], verts[5], verts[4]], [verts[2], verts[3], verts[7], verts[6]], 
        [verts[1], verts[2], verts[6], verts[5]], [verts[0], verts[3], verts[7], verts[4]]
    ]
    
    rect_collection = mplot3d.art3d.Poly3DCollection(faces, alpha=0.5)
    rect_collection.set_facecolor(params['color'])
    ax.add_collection3d(rect_collection)
    rects.append(rect_collection)

min_x, max_x = np.min(your_mesh.x), np.max(your_mesh.x)
min_y, max_y = np.min(your_mesh.y), np.max(your_mesh.y)
min_z, max_z = np.min(your_mesh.z), np.max(your_mesh.z)
ax.set_xlim([min_x, max_x])
ax.set_ylim([min_y, max_y])
ax.set_zlim([min_z, max_z])
ax.set_box_aspect([max_x-min_x, max_y-min_y, max_z-min_z])

# --- Fonction d'animation ---
def update(num):
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"Données reçues: '{line}'") 
            
            if line:
                values = [float(val) for val in line.split(',') if val]

                if len(values) == 6:
                    for i, value in enumerate(values):
                        color = plt.cm.bwr(norm(value))
                        rects[i].set_facecolor(color)
                else:
                    print(f"Attention: Nombre de valeurs incorrect. Reçu {len(values)}, attendu 6.")

    except (ValueError, serial.SerialException) as e:
        print(f"Erreur lors de la lecture des données: {e}")

    return rects

# Lancement de l'animation
ani = FuncAnimation(fig, update, interval=100)
plt.show()

ser.close()