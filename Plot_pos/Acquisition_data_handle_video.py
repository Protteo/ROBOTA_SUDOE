import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import time
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

# -------- CONFIGURATION --------
csv_path = "C:/Users/matte/OneDrive/Documents/Scolaire/Sigma//2A/Stage/ROBOTA SUDOE/Tactile_sensor/ROBOTA_SUDOE/Plot_pos/wrench_camera_data/wrench_camera_data/linear_y_hp1/wrench_data_2025-08-04_17-43-46.csv"          # chemin vers le fichier CSV
video_path = "C:/Users/matte/OneDrive/Documents/Scolaire/Sigma//2A/Stage/ROBOTA SUDOE/Tactile_sensor/ROBOTA_SUDOE/Plot_pos/wrench_camera_data/wrench_camera_data/linear_y_hp1/animation1_lineary_HP1.mp4"      # chemin d'enregistrement vidéo
lecture_freq = 500                          # fréquence en Hz (lignes lues / sec et fps)
duree_sec = 30                            # durée de la vidéo en secondes

# Colonnes CSV correspondant à chaque capteur (index 0-based)
# Exemple : capteur 0 = colonne 5, capteur 1 = colonne 12, etc.
colonnes_capteurs = [22, 23, 24, 25, 26, 27]

num_capteurs = len(colonnes_capteurs)

# -------- CHARGEMENT DES DONNÉES --------
data = pd.read_csv(csv_path, header=None)

if max(colonnes_capteurs) >= data.shape[1]:
    raise ValueError("Une des colonnes de capteurs dépasse le nombre de colonnes dans le CSV.")

# Extraire uniquement les colonnes nécessaires, dans l'ordre voulu
data_capteurs = data.iloc[:, colonnes_capteurs]

# -------- INITIALISATION DE LA FIGURE --------
fig, ax = plt.subplots(figsize=(6, 4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title("Zones de pression sur le manche")

# Positions des rectangles dans la figure (3 zones)
positions = [0.2, 0.5, 0.8]

# Chaque zone correspond à deux capteurs (top, bot) dans l'ordre donné
# Ex : (0, 2) = capteur 0 et capteur 2, etc.
# Attention : adapte si nécessaire selon ta définition
capteurs_zones = [(0, 2), (5, 4), (1, 3)]  # gauche, haut, droite

rects = {}
for i, x in enumerate(positions):
    rects[f"{i}_top"] = ax.add_patch(Rectangle((x - 0.05, 0.6), 0.1, 0.3, color='gray'))
    rects[f"{i}_bot"] = ax.add_patch(Rectangle((x - 0.05, 0.2), 0.1, 0.3, color='gray'))

green_red = LinearSegmentedColormap.from_list("green_red", ["blue", "red"])

# Fenêtre de moyenne glissante : 10 secondes
fenetre_temps = 10  # secondes
nb_points_fenetre = fenetre_temps * lecture_freq

# Texte timer
timer_text = ax.text(0.5, 0.95, "", ha='center', fontsize=16, color='red')

# -------- FONCTION DE MISE À JOUR --------
def update(frame):
    elapsed = frame / lecture_freq  # temps simulé en secondes
    timer_text.set_text(f"Temps: {int(elapsed)} s")

    start_idx = max(0, frame - nb_points_fenetre)
    end_idx = min(len(data_capteurs), frame)

    fenetre_data = data_capteurs.iloc[start_idx:end_idx]

    if fenetre_data.empty:
        return list(rects.values()) + [timer_text]

    for idx, (top_id, bot_id) in enumerate(capteurs_zones):
        moyenne_top = fenetre_data.iloc[:, top_id].mean()
        moyenne_bot = fenetre_data.iloc[:, bot_id].mean()
        rects[f"{idx}_top"].set_color(green_red(moyenne_top / 100))
        rects[f"{idx}_bot"].set_color(green_red(moyenne_bot / 100))

    # Arrêter l'animation si fin de durée ou fin données
    if elapsed >= duree_sec or end_idx >= len(data_capteurs):
        anim.event_source.stop()

    return list(rects.values()) + [timer_text]

# -------- ANIMATION --------
anim = animation.FuncAnimation(fig, update, frames=int(duree_sec * lecture_freq),
                               interval=1000/lecture_freq, blit=True)

# -------- ENREGISTREMENT --------
writer = animation.FFMpegWriter(fps=lecture_freq, metadata=dict(artist='ChatGPT'), bitrate=1800)

print(f"Démarrage de l'enregistrement vidéo vers : {video_path}")
anim.save(video_path, writer=writer)
print("Enregistrement terminé.")

plt.show()

#%%
import shutil

ffmpeg_path = shutil.which("ffmpeg")
print("FFmpeg trouvé ici :", ffmpeg_path)


