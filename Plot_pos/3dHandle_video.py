import pandas as pd
import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter
import matplotlib.pyplot as plt
import os
import time

# --- Paramètres de configuration (à ajuster) ---
CSV_FILE_PATH = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\wrench_camera_data\wrench_camera_data\linear_y_hp1\wrench_data_2025-08-04_17-43-46.csv"
STL_FILE_PATH = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\ROBOTA SUDOE 2025 BRIANCON-PROVERBIO\CAD\STL\Handle\Manche_couteau.STL"

# Correspondance entre les capteurs et les colonnes du fichier CSV
sensor_mapping = [21, 22, 23, 24, 25, 26]

rect_params = [
    {'x': 20, 'y': 20, 'z': 31, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 20, 'y': 20, 'z': 7, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 20, 'z': 31, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 20, 'z': 7, 'width': 60, 'height': 20, 'depth': 1},
    {'x': 85, 'y': 45, 'z': 8.8, 'width': 60, 'height': 1, 'depth': 20},
    {'x': 20, 'y': 45, 'z': 8.8, 'width': 60, 'height': 1, 'depth': 20}
]

# --- Paramètres de l'animation (à ajuster) ---
ANIMATION_DURATION_SECONDS = 30 # Durée totale de l'animation en secondes

# --- Variables de contrôle de l'animation ---
animation_running = False
current_frame_index = 0
data_to_plot = None
sensors_actors = []
color_map = None
norm = None

# --- Fonction de rappel pour l'animation ---
def update_animation():
    global current_frame_index, animation_running
    
    if not animation_running or data_to_plot is None:
        return

    if current_frame_index < len(data_to_plot):
        try:
            current_values = data_to_plot.iloc[current_frame_index, :].fillna(0).tolist()
            
            # Mise à jour des couleurs des capteurs
            for i, value in enumerate(current_values):
                color = color_map(norm(value))
                sensors_actors[i].prop.color = color

            print(f"Frame {current_frame_index + 1}/{len(data_to_plot)} - Valeurs: {current_values}")
            
            current_frame_index += 1
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'animation: {e}")
            animation_running = False
            
    else:
        print("Animation terminée. Appuyez sur Espace pour recommencer.")
        current_frame_index = 0
        animation_running = False

# --- Fonction pour démarrer/arrêter l'animation ---
def toggle_animation():
    global animation_running
    animation_running = not animation_running
    if animation_running:
        print("Animation démarrée. Appuyez sur Espace pour mettre en pause.")
    else:
        print("Animation en pause. Appuyez sur Espace pour reprendre.")
        
# --- Fonction principale ---
def main():
    global data_to_plot, sensors_actors, color_map, norm
    
    try:
        # 1. Lecture des données à partir du fichier CSV
        df = pd.read_csv(CSV_FILE_PATH, header=None).apply(pd.to_numeric, errors='coerce')
        data_to_plot = df.iloc[:, sensor_mapping]
        
        num_frames = len(data_to_plot)
        interval_ms = int(np.ceil((ANIMATION_DURATION_SECONDS * 1000) / num_frames))
        
        print(f"Total de données chargées : {num_frames}.")
        print(f"Intervalle d'affichage calculé : {interval_ms} ms par frame.")
        print(f"Durée totale de l'animation : {ANIMATION_DURATION_SECONDS} secondes.")
        print("Appuyez sur la touche ESPACE pour démarrer l'animation.")

    except FileNotFoundError:
        print(f"Erreur: Le fichier CSV '{CSV_FILE_PATH}' est introuvable.")
        return
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier CSV : {e}")
        return

    # 2. Initialisation du plotter PyVista
    plotter = BackgroundPlotter(title="Modélisation 3D du manche de couteau")
    
    try:
        pyvista_mesh = pv.read(STL_FILE_PATH)
        plotter.add_mesh(pyvista_mesh, color='white', smooth_shading=True)
    except FileNotFoundError:
        print(f"Erreur: Le fichier STL '{STL_FILE_PATH}' est introuvable.")
        plotter.close()
        return
        
    for params in rect_params:
        box = pv.Box(bounds=(params['x'], params['x'] + params['width'],
                             params['y'], params['y'] + params['height'],
                             params['z'], params['z'] + params['depth']))
        actor = plotter.add_mesh(box, color='blue', opacity=0.5)
        sensors_actors.append(actor)
        
    color_map = plt.get_cmap("bwr")
    norm = plt.Normalize(vmin=0, vmax=4096)
    
    # 3. Ajout du contrôle de l'animation
    plotter.add_key_event('space', toggle_animation)
    
    # Exécuter la fonction de mise à jour à l'intervalle calculé
    plotter.add_callback(update_animation, interval=interval_ms)

    try:
        plotter.app.exec()
    except KeyboardInterrupt:
        print("Fermeture de l'application.")
    finally:
        plotter.close()

if __name__ == '__main__':
    main()