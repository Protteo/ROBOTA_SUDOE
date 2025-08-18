import pyvista as pv
import numpy as np

# Chemins de vos fichiers STL
base_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Base.stl"
shoulder_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Shoulder.stl"
elbow_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Elbow.stl"
wrist1_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist1.stl"
wrist2_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist2.stl"

# Charger chaque maillage directement avec pyvista
base_pv = pv.read(base_path)
shoulder_pv = pv.read(shoulder_path)
elbow_pv = pv.read(elbow_path)
wrist1_pv = pv.read(wrist1_path)
wrist2_pv = pv.read(wrist2_path)

# Transformations pour positionner les pièces
# Les valeurs de translation et de rotation doivent être ajustées
# selon les dimensions réelles de votre modèle.
# Le paramètre 'inplace=True' modifie l'objet sur place pour éviter de recréer une nouvelle variable.
shoulder_pv.translate([0, 0, 0], inplace=True)
# shoulder_pv.rotate_x(90, inplace=True)

elbow_pv.translate([0, 0, 0], inplace=True)

wrist1_pv.translate([0, 0, 0], inplace=True)

wrist2_pv.translate([0, 0, 0], inplace=True)

# Créer un plotter pour afficher les maillages
plotter = pv.Plotter()
plotter.add_mesh(base_pv, color='lightblue', label='Base')
plotter.add_mesh(shoulder_pv, color='lightgreen', label='Shoulder')
plotter.add_mesh(elbow_pv, color='salmon', label='Elbow')
plotter.add_mesh(wrist1_pv, color='gold', label='Wrist1')
plotter.add_mesh(wrist2_pv, color='lightcoral', label='Wrist2')

# Afficher la fenêtre interactive
plotter.show()