import pyvista as pv
import numpy as np

# Chemins de vos fichiers STL
base_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Base.stl"
shoulder_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Shoulder.stl"
elbow_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Elbow.stl"
wrist1_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist1.stl"
wrist2_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist2.stl"

# Charger chaque maillage à l'état initial
original_meshes = {
    'Base': pv.read(base_path),
    'Shoulder': pv.read(shoulder_path),
    'Elbow': pv.read(elbow_path),
    'Wrist 1': pv.read(wrist1_path),
    'Wrist 2': pv.read(wrist2_path)
}

# Définir les points de pivot de chaque articulation
link_pivots = {
    'Shoulder': [0.0, 237.0, -135.0],
    'Elbow': [0.0, 875.0, 0.0],
    'Wrist 1': [0.0, 1377.0, 0.0],
    'Wrist 2': [0.0, 1390.0, -201.0],
}

# Créer un plotter
plotter = pv.Plotter(window_size=(1024, 768))
plotter.background_color = 'white'

# Dictionnaire pour stocker les acteurs PyVista
robot_actors = {}
robot_actors['Base'] = plotter.add_mesh(original_meshes['Base'], color='lightblue', label='Base')
robot_actors['Shoulder'] = plotter.add_mesh(original_meshes['Shoulder'], color='lightgreen', label='Shoulder')
robot_actors['Elbow'] = plotter.add_mesh(original_meshes['Elbow'], color='salmon', label='Elbow')
robot_actors['Wrist 1'] = plotter.add_mesh(original_meshes['Wrist 1'], color='gold', label='Wrist 1')
robot_actors['Wrist 2'] = plotter.add_mesh(original_meshes['Wrist 2'], color='lightcoral', label='Wrist 2')

# Dictionnaire pour stocker les angles des joints
joint_angles = {
    'Base': 0.0,
    'Shoulder': 0.0,
    'Elbow': 0.0,
    'Wrist 1': 0.0,
    'Wrist 2': 0.0
}

# Créez des maillages pour les repères de pivot une seule fois
pivot_meshes = {}
for name, pos in link_pivots.items():
    pivot_meshes[name] = pv.Sphere(radius=5).translate(pos)
    plotter.add_mesh(pivot_meshes[name], color='red', render_points_as_spheres=True, point_size=10.0)

# Ajouter des repères cartésiens pour chaque joint
base_axes = plotter.add_axes()
shoulder_axes = plotter.add_axes()
elbow_axes = plotter.add_axes()
wrist1_axes = plotter.add_axes()
wrist2_axes = plotter.add_axes()

def update_robot():
    # Définir les transformations individuelles de chaque maillon
    t_base = pv.Transform().rotate_y(joint_angles['Base'])
    t_shoulder = pv.Transform().rotate_z(joint_angles['Shoulder'], point=link_pivots['Shoulder'])
    t_elbow = pv.Transform().rotate_z(joint_angles['Elbow'], point=link_pivots['Elbow'])
    t_wrist1 = pv.Transform().rotate_z(joint_angles['Wrist 1'], point=link_pivots['Wrist 1'])
    t_wrist2 = pv.Transform().rotate_y(joint_angles['Wrist 2'], point=link_pivots['Wrist 2'])
    
    # Chaîne de transformations : chaque maillon se transforme
    # en fonction du maillon précédent
    final_transform_base = t_base.matrix
    final_transform_shoulder = final_transform_base @ t_shoulder.matrix
    final_transform_elbow = final_transform_shoulder @ t_elbow.matrix
    final_transform_wrist1 = final_transform_elbow @ t_wrist1.matrix
    final_transform_wrist2 = final_transform_wrist1 @ t_wrist2.matrix
    
    # Appliquer les transformations aux acteurs du plotter (non-destructif)
    robot_actors['Base'].user_matrix = final_transform_base
    robot_actors['Shoulder'].user_matrix = final_transform_shoulder
    robot_actors['Elbow'].user_matrix = final_transform_elbow
    robot_actors['Wrist 1'].user_matrix = final_transform_wrist1
    robot_actors['Wrist 2'].user_matrix = final_transform_wrist2

    # Mettre à jour la position des repères de pivot
    # On applique les transformations cumulatives aux points originaux
    pivot_meshes['Shoulder'].points = original_meshes['Shoulder'].translate(link_pivots['Shoulder']).transform(final_transform_base).points
    pivot_meshes['Elbow'].points = original_meshes['Elbow'].translate(link_pivots['Elbow']).transform(final_transform_shoulder).points
    pivot_meshes['Wrist 1'].points = original_meshes['Wrist 1'].translate(link_pivots['Wrist 1']).transform(final_transform_elbow).points
    pivot_meshes['Wrist 2'].points = original_meshes['Wrist 2'].translate(link_pivots['Wrist 2']).transform(final_transform_wrist1).points

    # Mettre à jour les matrices de transformation des axes en utilisant 'user_matrix'
    base_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_base)
    shoulder_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_shoulder)
    elbow_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_elbow)
    wrist1_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_wrist1)
    wrist2_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_wrist2)
    
    plotter.render()

# Fonction de rappel pour les curseurs
def update_callback(value, name):
    joint_angles[name] = value
    update_robot()

# Configuration des curseurs
slider_params = [
    ('Base', [-180, 180], 0.0),
    ('Shoulder', [-180, 180], 0.0),
    ('Elbow', [-180, 180], 0.0),
    ('Wrist 1', [-180, 180], 0.0),
    ('Wrist 2', [-180, 180], 0.0),
]

# Calculer l'espacement pour les curseurs
num_sliders = len(slider_params)
spacing = 0.15  # Un espacement plus grand pour éviter le chevauchement
start_y = 0.1
end_y = start_y + (num_sliders - 1) * spacing

# Ajout des curseurs au plotter
for i, (name, rng, value) in enumerate(slider_params):
    plotter.add_slider_widget(
        callback=lambda value, name=name: update_callback(value, name),
        rng=rng,
        title=name,
        pointa=(0.02, start_y + i * spacing),
        pointb=(0.32, start_y + i * spacing),
        value=value,
        style='modern'
    )
    
# IMPORTANT : Appel initial pour positionner les repères avant l'affichage
update_robot()

# Afficher la fenêtre en mode interactif
plotter.show(interactive=True, auto_close=False)