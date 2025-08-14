import pyvista as pv
from pyvistaqt import BackgroundPlotter
import serial
import time
import numpy as np
from stl import mesh
import matplotlib.pyplot as plt

# --- Paramètres de configuration (à ajuster) ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
STL_FILE_PATH = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\ROBOTA SUDOE 2025 BRIANCON-PROVERBIO\CAD\STL\Handle\Manche_couteau.STL"

rect_params = [
    {'x': 20, 'y': 20, 'z': 31, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 20, 'y': 20, 'z': 7, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 20, 'z': 31, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 20, 'z': 7, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 45, 'z': 8.8, 'width': 60, 'height': 1, 'depth': 20},
    {'x': 20, 'y': 45, 'z': 8.8, 'width': 60, 'height': 1, 'depth': 20}
]

# --- Fonction principale d'affichage 3D et de lecture ---
def main():
    # Initialisation de la scène PyVista avec BackgroundPlotter
    plotter = BackgroundPlotter()

    # Chargement et affichage du maillage STL
    try:
        pyvista_mesh = pv.read(STL_FILE_PATH)
        plotter.add_mesh(pyvista_mesh, color='white', smooth_shading=True)
    except FileNotFoundError:
        print(f"Erreur: Le fichier STL '{STL_FILE_PATH}' est introuvable.")
        return
        
    sensors_actors = []
    for params in rect_params:
        box = pv.Box(bounds=(params['x'], params['x'] + params['width'],
                             params['y'], params['y'] + params['height'],
                             params['z'], params['z'] + params['depth']))
        actor = plotter.add_mesh(box, color='blue', opacity=0.5)
        sensors_actors.append(actor)
        
    color_map = plt.get_cmap("bwr")
    norm = plt.Normalize(vmin=0, vmax=4096)
    
    # Initialisation de la connexion série
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        ser.reset_input_buffer()
        print(f"Connexion au port série réussie sur {SERIAL_PORT}.")
    except serial.SerialException as e:
        print(f"Erreur de connexion au port série {SERIAL_PORT}: {e}")
        return

    # Boucle d'animation principale
    try:
        while True:
            # Vérifie si le plotter est fermé
            if plotter._closed:
                break
            
            # Lecture des données série
            line = ser.readline().decode('utf-8').strip()
            if line:
                try:
                    new_values = [float(val) for val in line.split(',') if val]
                    if len(new_values) == 6:
                        print(f"Données reçues: {new_values}")
                        for i, value in enumerate(new_values):
                            color = color_map(norm(value))
                            sensors_actors[i].prop.color = color
                except (ValueError, IndexError) as e:
                    print(f"Erreur de format de données: {line} - {e}")
            
            # Mettre à jour l'affichage
            plotter.app.processEvents()
            plotter.render()
    
    except KeyboardInterrupt:
        print("Arrêt de l'application.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        plotter.close()

if __name__ == '__main__':
    main()