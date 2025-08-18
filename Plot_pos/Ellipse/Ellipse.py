import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5 import QtWidgets, QtCore
import sys
import numpy as np

# Chemins de vos fichiers STL
base_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Base.stl"
shoulder_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Shoulder.stl"
elbow_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Elbow.stl"
wrist1_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist1.stl"
wrist2_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist2.stl"

# Définition des points de pivot
link_pivots = {
    'Shoulder': [0.0, 237.0, -135.0],
    'Elbow': [0.0, 875.0, 0.0],
    'Wrist 1': [0.0, 1377.0, 0.0],
    'Wrist 2': [0.0, 1390.0, -201.0],
}

# Charger les maillages
original_meshes = {
    'Base': pv.read(base_path),
    'Shoulder': pv.read(shoulder_path),
    'Elbow': pv.read(elbow_path),
    'Wrist 1': pv.read(wrist1_path),
    'Wrist 2': pv.read(wrist2_path)
}

class RobotApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(RobotApp, self).__init__(parent)
        self.setWindowTitle("Contrôle du robot avec PyVista et PyQt")
        
        # Variables pour les angles
        self.joint_angles = {
            'Base': 0.0, 'Shoulder': 0.0, 'Elbow': 0.0, 'Wrist 1': 0.0, 'Wrist 2': 0.0
        }

        # Création des widgets de la fenêtre principale
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)

        # Création du plotter PyVista
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter)

        # Création du panneau de contrôle des angles
        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)
        main_layout.addWidget(control_panel)

        self.entries = {}
        for name, value in self.joint_angles.items():
            entry_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(f"Angle {name}:")
            entry = QtWidgets.QLineEdit(str(value))
            entry.returnPressed.connect(lambda n=name, e=entry: self.on_text_entry(n, e))
            
            self.entries[name] = entry
            
            entry_layout.addWidget(label)
            entry_layout.addWidget(entry)
            control_layout.addLayout(entry_layout)

        # Initialisation du robot
        self.setup_robot_scene()

    def setup_robot_scene(self):
        # Initialisation de la scène PyVista
        self.plotter.background_color = 'white'
        self.robot_actors = {
            'Base': self.plotter.add_mesh(original_meshes['Base'], color='lightblue', label='Base'),
            'Shoulder': self.plotter.add_mesh(original_meshes['Shoulder'], color='lightgreen', label='Shoulder'),
            'Elbow': self.plotter.add_mesh(original_meshes['Elbow'], color='salmon', label='Elbow'),
            'Wrist 1': self.plotter.add_mesh(original_meshes['Wrist 1'], color='gold', label='Wrist 1'),
            'Wrist 2': self.plotter.add_mesh(original_meshes['Wrist 2'], color='lightcoral', label='Wrist 2')
        }
        
        self.pivot_meshes = {}
        for name, pos in link_pivots.items():
            self.pivot_meshes[name] = pv.Sphere(radius=5).translate(pos)
            self.plotter.add_mesh(self.pivot_meshes[name], color='red', render_points_as_spheres=True, point_size=10.0)

        self.base_axes = self.plotter.add_axes()
        self.shoulder_axes = self.plotter.add_axes()
        self.elbow_axes = self.plotter.add_axes()
        self.wrist1_axes = self.plotter.add_axes()
        self.wrist2_axes = self.plotter.add_axes()

        # Ajout des curseurs PyVista
        slider_params = [
            ('Base', [-180, 180], 0.0), ('Shoulder', [-180, 180], 0.0), ('Elbow', [-180, 180], 0.0),
            ('Wrist 1', [-180, 180], 0.0), ('Wrist 2', [-180, 180], 0.0)
        ]
        num_sliders = len(slider_params)
        spacing = 0.15
        start_y = 0.1
        for i, (name, rng, value) in enumerate(slider_params):
            self.plotter.add_slider_widget(
                callback=lambda val, n=name: self.on_slider_change(val, n),
                rng=rng, title=name, pointa=(0.02, start_y + i * spacing), pointb=(0.32, start_y + i * spacing),
                value=value, style='modern'
            )
        
        self.update_robot()

    def update_robot(self):
        # Code de mise à jour de la position du robot (inchangé)
        t_base = pv.Transform().rotate_y(self.joint_angles['Base'])
        t_shoulder = pv.Transform().rotate_z(self.joint_angles['Shoulder'], point=link_pivots['Shoulder'])
        t_elbow = pv.Transform().rotate_z(self.joint_angles['Elbow'], point=link_pivots['Elbow'])
        t_wrist1 = pv.Transform().rotate_z(self.joint_angles['Wrist 1'], point=link_pivots['Wrist 1'])
        t_wrist2 = pv.Transform().rotate_y(self.joint_angles['Wrist 2'], point=link_pivots['Wrist 2'])
        
        final_transform_base = t_base.matrix
        final_transform_shoulder = final_transform_base @ t_shoulder.matrix
        final_transform_elbow = final_transform_shoulder @ t_elbow.matrix
        final_transform_wrist1 = final_transform_elbow @ t_wrist1.matrix
        final_transform_wrist2 = final_transform_wrist1 @ t_wrist2.matrix
        
        self.robot_actors['Base'].user_matrix = final_transform_base
        self.robot_actors['Shoulder'].user_matrix = final_transform_shoulder
        self.robot_actors['Elbow'].user_matrix = final_transform_elbow
        self.robot_actors['Wrist 1'].user_matrix = final_transform_wrist1
        self.robot_actors['Wrist 2'].user_matrix = final_transform_wrist2
        
        self.pivot_meshes['Shoulder'].points = original_meshes['Shoulder'].translate(link_pivots['Shoulder']).transform(final_transform_base).points
        self.pivot_meshes['Elbow'].points = original_meshes['Elbow'].translate(link_pivots['Elbow']).transform(final_transform_shoulder).points
        self.pivot_meshes['Wrist 1'].points = original_meshes['Wrist 1'].translate(link_pivots['Wrist 1']).transform(final_transform_elbow).points
        self.pivot_meshes['Wrist 2'].points = original_meshes['Wrist 2'].translate(link_pivots['Wrist 2']).transform(final_transform_wrist1).points
        
        self.base_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_base)
        self.shoulder_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_shoulder)
        self.elbow_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_elbow)
        self.wrist1_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_wrist1)
        self.wrist2_axes.user_matrix = pv.vtkmatrix_from_array(final_transform_wrist2)
        
        self.plotter.render()
        
    def on_slider_change(self, value, name):
        """Met à jour l'angle et le champ de texte depuis le curseur."""
        self.joint_angles[name] = value
        self.entries[name].setText(f"{value:.2f}")
        self.update_robot()

    def on_text_entry(self, name, entry):
        """Met à jour l'angle depuis le champ de texte."""
        try:
            value = float(entry.text())
            self.joint_angles[name] = value
            self.update_robot()
            print(f"Angle {name} mis à jour à {value} degrés.")
        except ValueError:
            print(f"Valeur invalide pour {name}. Veuillez entrer un nombre.")

if __name__ == '__main__':
    # Nécessite d'installer PyQt5 et pyvistaqt
    # pip install PyQt5 pyvistaqt
    app = QtWidgets.QApplication(sys.argv)
    window = RobotApp()
    window.show()
    sys.exit(app.exec_())