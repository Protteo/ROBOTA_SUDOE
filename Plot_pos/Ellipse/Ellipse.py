import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5 import QtWidgets, QtCore
import sys
import os
import numpy as np

# Ajoute le répertoire où se trouve robot_kinematics.py
chemin_du_repertoire = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse"
sys.path.append(os.path.abspath(chemin_du_repertoire))

from robot_kinematics import calculate_jacobian, a, d, alpha

# Chemins de vos fichiers STL
base_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Base.stl"
shoulder_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Shoulder.stl"
elbow_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Elbow.stl"
wrist1_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist1.stl"
wrist2_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist2.stl"

# Définition des points de pivot (inchangé)
link_pivots = {
    'Shoulder': np.array([0.0, 237.0, -135.0]),
    'Elbow': np.array([0.0, 875.0, 0.0]),
    'Wrist 1': np.array([0.0, 1377.0, 0.0]),
    'Wrist 2': np.array([0.0, 1390.0, -201.0]),
}

# Charger et décaler les maillages
original_meshes = {
    'Base': pv.read(base_path),
    'Shoulder': pv.read(shoulder_path),
    'Elbow': pv.read(elbow_path),
    'Wrist 1': pv.read(wrist1_path),
    'Wrist 2': pv.read(wrist2_path)
}

shoulder_offset = -link_pivots['Shoulder']
elbow_offset = -link_pivots['Elbow']
wrist1_offset = -link_pivots['Wrist 1']
wrist2_offset = -link_pivots['Wrist 2']

initial_meshes = {
    'Base': original_meshes['Base'],
    'Shoulder': original_meshes['Shoulder'].translate(shoulder_offset),
    'Elbow': original_meshes['Elbow'].translate(elbow_offset),
    'Wrist 1': original_meshes['Wrist 1'].translate(wrist1_offset),
    'Wrist 2': original_meshes['Wrist 2'].translate(wrist2_offset)
}

class RobotApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(RobotApp, self).__init__(parent)
        self.setWindowTitle("Contrôle du robot avec PyVista et PyQt")

        self.joint_angles = {
            'Base': 0.0, 'Shoulder': 45.0, 'Elbow': 45.0, 'Wrist 1': 0.0, 'Wrist 2': 0.0
        }
        
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        
        self.plotter = QtInteractor(self)
        
        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.plotter)
        splitter.addWidget(control_panel)

        splitter.setStretchFactor(0, 3) 
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        
        controllable_joints = ['Base', 'Shoulder', 'Elbow', 'Wrist 1', 'Wrist 2']
        
        self.entries = {}
        for name in controllable_joints:
            entry_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(f"Angle {name}:")
            entry = QtWidgets.QLineEdit(str(self.joint_angles[name]))
            entry.returnPressed.connect(lambda n=name, e=entry: self.on_text_entry(n, e))
            self.entries[name] = entry
            entry_layout.addWidget(label)
            entry_layout.addWidget(entry)
            control_layout.addLayout(entry_layout)

        self.manip_ellipsoid_actor = None
        self.effector_marker = None
        self.setup_robot_scene()

    def setup_robot_scene(self):
        self.plotter.background_color = 'white'
        self.robot_actors = {
            'Base': self.plotter.add_mesh(initial_meshes['Base'], color='lightblue', label='Base'),
            'Shoulder': self.plotter.add_mesh(initial_meshes['Shoulder'], color='lightgreen', label='Shoulder'),
            'Elbow': self.plotter.add_mesh(initial_meshes['Elbow'], color='salmon', label='Elbow'),
            'Wrist 1': self.plotter.add_mesh(initial_meshes['Wrist 1'], color='gold', label='Wrist 1'),
            'Wrist 2': self.plotter.add_mesh(initial_meshes['Wrist 2'], color='lightcoral', label='Wrist 2')
        }
        
        self.pivot_meshes = {}
        for name, pos in link_pivots.items():
            self.pivot_meshes[name] = pv.Sphere(radius=5).translate(pos)
            self.plotter.add_mesh(self.pivot_meshes[name], color='red', render_points_as_spheres=True, point_size=10.0)

        slider_params = [
            ('Base', [-180, 180], self.joint_angles['Base']), 
            ('Shoulder', [-180, 180], self.joint_angles['Shoulder']), 
            ('Elbow', [-180, 180], self.joint_angles['Elbow']),
            ('Wrist 1', [-180, 180], self.joint_angles['Wrist 1']), 
            ('Wrist 2', [-180, 180], self.joint_angles['Wrist 2'])
        ]
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
        t_base = pv.Transform().rotate_y(self.joint_angles['Base'])
        t_shoulder = pv.Transform().rotate_z(self.joint_angles['Shoulder'])
        t_elbow = pv.Transform().rotate_z(self.joint_angles['Elbow'])
        t_wrist1 = pv.Transform().rotate_z(self.joint_angles['Wrist 1'])
        t_wrist2 = pv.Transform().rotate_y(self.joint_angles['Wrist 2'])
        
        final_transform_base = t_base.matrix
        final_transform_shoulder = final_transform_base @ pv.Transform().translate(link_pivots['Shoulder']).matrix @ t_shoulder.matrix
        final_transform_elbow = final_transform_shoulder @ pv.Transform().translate(link_pivots['Elbow'] - link_pivots['Shoulder']).matrix @ t_elbow.matrix
        final_transform_wrist1 = final_transform_elbow @ pv.Transform().translate(link_pivots['Wrist 1'] - link_pivots['Elbow']).matrix @ t_wrist1.matrix
        final_transform_wrist2 = final_transform_wrist1 @ pv.Transform().translate(link_pivots['Wrist 2'] - link_pivots['Wrist 1']).matrix @ t_wrist2.matrix
        
        self.robot_actors['Base'].user_matrix = final_transform_base
        self.robot_actors['Shoulder'].user_matrix = final_transform_shoulder
        self.robot_actors['Elbow'].user_matrix = final_transform_elbow
        self.robot_actors['Wrist 1'].user_matrix = final_transform_wrist1
        self.robot_actors['Wrist 2'].user_matrix = final_transform_wrist2

        q_angles_deg = np.array(list(self.joint_angles.values()))
        
        try:
            jacobien = calculate_jacobian(q_angles_deg, a, d, alpha)
            
            wrist2_transform_matrix = self.robot_actors['Wrist 2'].user_matrix
            self.calculate_and_plot_ellipsoid(jacobien, wrist2_transform_matrix, scale_factor=250)
        except Exception as e:
            print(f"Erreur lors du calcul de la cinématique ou de l'affichage de l'ellipsoïde : {e}")
            
        self.plotter.render()
        
    def on_slider_change(self, value, name):
        self.joint_angles[name] = value
        self.entries[name].setText(f"{value:.2f}")
        self.update_robot()

    def on_text_entry(self, name, entry):
        try:
            value = float(entry.text())
            self.joint_angles[name] = value
            self.update_robot()
        except ValueError:
            print(f"Valeur invalide pour {name}. Veuillez entrer un nombre.")

    def calculate_and_plot_ellipsoid(self, jacobien, wrist2_transform_matrix, scale_factor=250):
        Jv = jacobien[:3, :]
        
        try:
            U, s, Vt = np.linalg.svd(Jv)
            
            if np.isclose(s[0], 0, atol=1e-6):
                if self.manip_ellipsoid_actor:
                    self.plotter.remove_actor(self.manip_ellipsoid_actor)
                print("Le robot est dans une configuration singulière. L'ellipsoïde de manipulabilité ne peut pas être affiché.")
                return

            s_scaled = s / s[0] * scale_factor

            if self.manip_ellipsoid_actor:
                self.plotter.remove_actor(self.manip_ellipsoid_actor)

            ellipsoid_mesh = pv.Sphere(radius=1.0, phi_resolution=30, theta_resolution=30)
            
            # Paramètre pour le positionnement manuel de l'ellipse
            # decalage_local_ellipse = np.array([0.0, 1535.0, -300.0])
            decalage_local_ellipse = np.array([0.0, 150.0, -100.0])

            ellipsoid_mesh.scale(s_scaled, inplace=True)
            ellipsoid_mesh.translate(decalage_local_ellipse, inplace=True)
            ellipsoid_mesh.transform(wrist2_transform_matrix, inplace=True)

            self.manip_ellipsoid_actor = self.plotter.add_mesh(ellipsoid_mesh, color='red', opacity=0.5, style='wireframe')
            
        except np.linalg.LinAlgError:
            if self.manip_ellipsoid_actor:
                self.plotter.remove_actor(self.manip_ellipsoid_actor)
            print("Erreur de calcul SVD : Le robot est dans une configuration singulière.")
        except Exception as e:
            print(f"Erreur lors de l'affichage de l'ellipsoïde : {e}")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = RobotApp()
    window.show()
    sys.exit(app.exec_())