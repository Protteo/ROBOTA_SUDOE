import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

"""This code gets the data from a csv file after the movement, and then it creates a 30s video of a color mapping about the 6 sensors on the handle."""


# -------- CONFIGURATION --------
csv_path = "C:/Users/matte/OneDrive/Documents/Scolaire/Sigma//2A/Stage/ROBOTA SUDOE/Tactile_sensor/ROBOTA_SUDOE/Plot_pos/wrench_camera_data/wrench_camera_data/slow_linear_y_hp1/wrench_data_2025-08-05_11-27-48.csv"
video_path = "C:/Users/matte/OneDrive/Documents/Scolaire/Sigma//2A/Stage/ROBOTA SUDOE/Tactile_sensor/ROBOTA_SUDOE/Plot_pos/wrench_camera_data/wrench_camera_data/slow_linear_y_hp1/animation6_slow_linear_y_HP1.mp4"
duree_sec = 30  # durée de la vidéo en secondes
nb_frames = 500  # nombre total d'images dans la vidéo
fps = nb_frames / duree_sec  # fréquence d'images pour avoir pile 30s → 16.67 fps

# Colonnes capteurs dans CSV
colonnes_capteurs = [22, 23, 24, 25, 26, 27]
num_capteurs = len(colonnes_capteurs)

# -------- CHARGEMENT DES DONNÉES --------
data = pd.read_csv(csv_path, header=None)
if max(colonnes_capteurs) >= data.shape[1]:
    raise ValueError("Une des colonnes de capteurs dépasse le nombre de colonnes dans le CSV.")
data_capteurs = data.iloc[:, colonnes_capteurs].apply(pd.to_numeric, errors='coerce')

# -------- INITIALISATION FIGURE --------
fig, ax = plt.subplots(figsize=(6, 4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title("Pressure zone on the handle.")

# Positions rectangles : gauche, haut, droite
positions = [0.2, 0.5, 0.8]
capteurs_zones = [(0, 2), (5, 4), (1, 3)]  # (top_id, bot_id) pour chaque zone

rects = {}
for i, x in enumerate(positions):
    rects[f"{i}_top"] = ax.add_patch(Rectangle((x - 0.05, 0.6), 0.1, 0.3, color='gray'))
    rects[f"{i}_bot"] = ax.add_patch(Rectangle((x - 0.05, 0.2), 0.1, 0.3, color='gray'))

# Couleurs pression
green_red = LinearSegmentedColormap.from_list("green_red", ["blue", "red"])

# Texte timer
timer_text = ax.text(0.5, 0.95, "", ha='center', fontsize=16, color='red')

# -------- PRÉPARATION DES FRAMES --------
total_points = len(data_capteurs)
indices_frames = np.linspace(0, total_points - 1, nb_frames, dtype=int)

# Fenêtre glissante : 10s sur 500Hz → 5000 points
lecture_freq_original = 500
fenetre_points = lecture_freq_original * 10

# -------- FONCTION D’UPDATE --------
def update(frame_idx):
    idx = indices_frames[frame_idx]
    elapsed = frame_idx * (duree_sec / nb_frames)
    timer_text.set_text(f"Temps: {elapsed:.1f} s")

    start_idx = max(0, idx - fenetre_points)
    fenetre_data = data_capteurs.iloc[start_idx:idx+1]

    for i, (top_id, bot_id) in enumerate(capteurs_zones):
        moyenne_top = fenetre_data.iloc[:, top_id].mean()
        moyenne_bot = fenetre_data.iloc[:, bot_id].mean()

        # Normalisation simple, évite dépassement >1
        moyenne_top = np.clip(moyenne_top / 100, 0, 1)
        moyenne_bot = np.clip(moyenne_bot / 100, 0, 1)

        rects[f"{i}_top"].set_color(green_red(moyenne_top))
        rects[f"{i}_bot"].set_color(green_red(moyenne_bot))

    return list(rects.values()) + [timer_text]

# -------- ANIMATION --------
anim = animation.FuncAnimation(fig, update, frames=nb_frames, blit=True)

# -------- ENREGISTREMENT --------
writer = animation.FFMpegWriter(fps=fps, metadata=dict(artist='ChatGPT'), bitrate=1800)
print(f"Starting the video saving into : {video_path}")
anim.save(video_path, writer=writer, dpi=200)
print("Saving over")
