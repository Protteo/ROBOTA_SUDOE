import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from stl import mesh
import threading
from queue import Queue

# --- Paramètres de configuration ---
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

# File d'attente pour la communication entre les threads
data_queue = Queue()
stop_thread = threading.Event()

# --- Fonction de lecture du port série dans un thread séparé ---
def read_serial_data():
    """Lit les données du port série et met à jour la file d'attente."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        ser.reset_input_buffer()
        print(f"Thread de lecture série démarré sur {SERIAL_PORT}")
        
        while not stop_thread.is_set():
            # Vidage du buffer si des données s'y accumulent
            if ser.in_waiting > 0:
                ser.reset_input_buffer()
                
            line = ser.readline().decode('utf-8').strip()
            if line:
                try:
                    new_values = [float(val) for val in line.split(',') if val]
                    if len(new_values) == 6:
                        data_queue.put(new_values)
                except (ValueError, IndexError) as e:
                    print(f"Erreur de format de données: {line} - {e}")
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"Erreur fatale dans le thread série: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

# --- Fonction principale ---
def main():
    serial_thread = threading.Thread(target=read_serial_data, daemon=True)
    serial_thread.start()
    
    plotter = BackgroundPlotter(title="Modélisation 3D du manche de couteau")
    
    try:
        pyvista_mesh = pv.read(STL_FILE_PATH)
        plotter.add_mesh(pyvista_mesh, color='white', smooth_shading=True)
    except FileNotFoundError:
        print(f"Erreur: Le fichier STL '{STL_FILE_PATH}' est introuvable.")
        stop_thread.set()
        serial_thread.join()
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

    def update_colors():
        last_values = None
        while not data_queue.empty():
            last_values = data_queue.get_nowait()
        
        if last_values:
            print(f"Données mises à jour: {last_values}")
            try:
                for i, value in enumerate(last_values):
                    color = color_map(norm(value))
                    sensors_actors[i].prop.color = color
            except Exception as e:
                print(f"Erreur lors de la mise à jour des couleurs: {e}")

    plotter.add_callback(update_colors, interval=50)
    
    try:
        plotter.app.exec()
    except KeyboardInterrupt:
        print("Fermeture de l'application.")
    finally:
        stop_thread.set()
        serial_thread.join()
        if 'ser' in locals() and ser.is_open:
            ser.close()
        plotter.close()

if __name__ == '__main__':
    main()