import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5 import QtWidgets, QtCore
import sys
import os
import numpy as np
from scipy.spatial.transform import Rotation as R
import vtk
import pygame

# Chemins de vos fichiers STL
base_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Base.stl"
shoulder_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Shoulder.stl"
elbow_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Elbow.stl"
wrist1_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist1.stl"
wrist2_path = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\Tactile_sensor\ROBOTA_SUDOE\Plot_pos\Ellipse\704-244-01_filled_A\Wrist2.stl"

# Définition des points de pivot
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

# Décalage de l'effecteur final
end_effector_offset = np.array([0.0, 150.0, -100.0])

def calculate_geometric_jacobian(transforms, tool_center):
    J = np.zeros((6, 5))
    p_end_effector = tool_center
    
    rotation_axes_local = {
        'Base': np.array([0, 1, 0]),
        'Shoulder': np.array([0, 0, 1]),
        'Elbow': np.array([0, 0, 1]),
        'Wrist 1': np.array([0, 0, 1]),
        'Wrist 2': np.array([0, 1, 0])
    }
    
    pivots_global = [np.array([0, 0, 0])]
    for i in range(len(transforms) - 1):
        pivots_global.append(transforms[i][:3, 3])
    
    z_axes_global = []
    z_base = rotation_axes_local['Base']
    z_axes_global.append(z_base)
    
    link_names = ['Shoulder', 'Elbow', 'Wrist 1', 'Wrist 2']
    for i, name in enumerate(link_names):
        R_i = transforms[i][:3, :3]
        z_i = R_i @ rotation_axes_local[name]
        z_axes_global.append(z_i)

    for i in range(5):
        J[:3, i] = np.cross(z_axes_global[i], p_end_effector - pivots_global[i])
        J[3:, i] = z_axes_global[i]
        
    return J

class RobotApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(RobotApp, self).__init__(parent)
        self.setWindowTitle("Contrôle du robot avec PyVista et PyQt")

        self.joint_angles = {
            'Base': 0.0, 'Shoulder': 45.0, 'Elbow': 45.0, 'Wrist 1': 0.0, 'Wrist 2': 0.0
        }
        
        pygame.init()
        pygame.joystick.init()
        
        self.joysticks = []
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            print(f"{joystick_count} joystick(s) détecté(s).")
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.joysticks.append(joystick)
                print(f"Joystick {i} initialisé : {joystick.get_name()}")
        else:
            print("Aucun joystick détecté.")
        
        self.manipulation_center_pos = np.array([0.0, 145.0, -100.0])
        self.last_key_press_time = 0.0

        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        
        self.plotter = QtInteractor(self)
        self.plotter_style = self.plotter.interactor.GetInteractorStyle()

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
            entry.setReadOnly(True)
            self.entries[name] = entry
            entry_layout.addWidget(label)
            entry_layout.addWidget(entry)
            control_layout.addLayout(entry_layout)

        self.manip_ellipsoid_actor = None
        self.effector_marker_actor = None 
        self.is_dragging = False
        self.mouse_pos_prev = None
        self.initial_effector_pos = None
        self.effector_marker_name = 'effector_marker'
        self.manipulation_cylinders = {}
        self.active_tool = None
        
        self.trans_height = 100
        self.trans_radius = 10
        self.rot_height = 2
        self.rot_radius = 100

        self.setup_manipulation_cylinders() 
        self.setup_robot_scene()
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_joystick_control)
        self.timer.start(75) 
        
        self.update_robot()
        
        self.last_print_time = 0

    def update_joystick_control(self):
        if len(self.joysticks) < 2:
            return

        pygame.event.pump()
        current_time = pygame.time.get_ticks()

        deadzone = 0.1
        translation_speed = 5.0
        
        # --- Lecture et gestion des axes du Joystick 0 (Translation) ---
        trans_x_raw = self.joysticks[0].get_axis(0)
        trans_y_raw = self.joysticks[0].get_axis(1)
        
        trans_z_raw = 0.0
        if self.joysticks[0].get_numaxes() > 2:
            trans_z_raw = self.joysticks[0].get_axis(2)
        
        trans_x = trans_x_raw if abs(trans_x_raw) > deadzone else 0.0
        trans_y = trans_y_raw if abs(trans_y_raw) > deadzone else 0.0
        trans_z = trans_z_raw if abs(trans_z_raw) > deadzone else 0.0
        
        # Les vitesses de rotation sont nulles pour l'instant
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0
        
        # Créer le vecteur de vitesse souhaité dans le repère global
        # Mouvements en X, Y et Z du repère global
        desired_dx_global = np.array([trans_x * translation_speed, trans_y * translation_speed, 0.0])

        # Créer un vecteur de vitesse complet (linéaire et angulaire) dans le repère de l'effecteur
        # L'orientation ne change pas donc les vitesses angulaires sont nulles
        desired_dx_local = np.zeros(6)
        
        # On projette le mouvement global sur le repère de l'effecteur
        current_effector_matrix = self.transforms[-1]
        R_effector_global = current_effector_matrix[:3, :3]
        desired_dx_local[:3] = R_effector_global.T @ desired_dx_global

        if np.allclose(desired_dx_local, np.zeros(6), atol=0.01):
            dq = np.zeros(5)
        else:
            current_effector_pos = current_effector_matrix[:3, 3] + end_effector_offset
            J = calculate_geometric_jacobian(self.transforms, current_effector_pos)
            
            # Utilisation de la pseudo-inverse amortie
            lambda_damping = 0.25 
            J_damped = J.T @ J + lambda_damping * np.eye(J.shape[1])
            J_pinv = np.linalg.inv(J_damped) @ J.T

            # Calcul du mouvement principal
            dq_principal = J_pinv @ desired_dx_local
            
            # --- CALCUL DE LA PROJECTION DE L'ESPACE NUL ---
            # Objectif secondaire : minimiser les rotations de l'effecteur
            # On veut que la vitesse de rotation de l'effecteur soit nulle.
            # Le vecteur de vitesse de rotation souhaitée est [0, 0, 0].
            # L'erreur est la vitesse de rotation actuelle de l'effecteur, mais on veut
            # la minimiser pour une orientation fixe.
            
            # Le vecteur de vitesse d'erreur pour la tâche secondaire
            # On cherche a minimiser les vitesses articulaires (plus simple et plus stable pour ce cas)
            desired_dq_secondary = np.zeros(5) 
            
            # Calcul du projecteur de l'espace nul
            I = np.eye(J_pinv.shape[0])
            P = I - J_pinv @ J
            
            # Calcul du mouvement secondaire en utilisant la pseudo-inverse et le projecteur de l'espace nul
            # Le projecteur garantit que ce mouvement n'interfère pas avec la tâche principale
            dq_secondary = P @ desired_dq_secondary
            
            # Combinaison des deux mouvements
            dq = dq_principal + dq_secondary
            # --- FIN DU CALCUL DE L'ESPACE NUL ---

        q_angles_deg = np.array(list(self.joint_angles.values()))
        q_angles_deg += np.rad2deg(dq)
        
        self.update_robot(q_angles_deg)
        self.update_manipulation_cylinders()
        
    def print_joystick_status(self):
        """Affiche les valeurs de tous les axes, boutons et hats pour chaque joystick."""
        print("-" * 20)
        for i, joystick in enumerate(self.joysticks):
            print(f"État du Joystick {i} ({joystick.get_name()}):")
            
            num_axes = joystick.get_numaxes()
            if num_axes > 0:
                print("  Axes :")
            for axis_idx in range(num_axes):
                axis_value = joystick.get_axis(axis_idx)
                print(f"    Axe {axis_idx}: {axis_value:.4f}")
            
            num_buttons = joystick.get_numbuttons()
            if num_buttons > 0:
                print("  Boutons :")
            for button_idx in range(num_buttons):
                button_state = joystick.get_button(button_idx)
                if button_state:
                    print(f"    Bouton {button_idx}: ENFONCÉ")

            num_hats = joystick.get_numhats()
            if num_hats > 0:
                print("  Hats :")
            for hat_idx in range(num_hats):
                hat_state = joystick.get_hat(hat_idx)
                if hat_state != (0, 0):
                    print(f"    Hat {hat_idx}: {hat_state}")
        print("-" * 20)
        
    def _solve_ik_iteratively(self, desired_effector_transform_matrix):
        pass

    def reset_interactor_style(self):
        self.plotter.interactor.SetInteractorStyle(self.plotter_style)
        
    def setup_manipulation_cylinders(self):
        trans_height = 100
        trans_radius = 10
        
        trans_x_mesh = pv.Cylinder(direction=(1, 0, 0), height=trans_height, radius=trans_radius)
        trans_neg_x_mesh = pv.Cylinder(direction=(-1, 0, 0), height=trans_height, radius=trans_radius)
        trans_y_mesh = pv.Cylinder(direction=(0, 1, 0), height=trans_height, radius=trans_radius)
        trans_neg_y_mesh = pv.Cylinder(direction=(0, -1, 0), height=trans_height, radius=trans_radius)
        trans_z_mesh = pv.Cylinder(direction=(0, 0, 1), height=trans_height, radius=trans_radius)
        trans_neg_z_mesh = pv.Cylinder(direction=(0, 0, -1), height=trans_height, radius=trans_radius)

        self.manipulation_cylinders['trans_x'] = self.plotter.add_mesh(trans_x_mesh, color='red', pickable=True, name='trans_x', render=False, opacity=0.8)
        self.manipulation_cylinders['trans_neg_x'] = self.plotter.add_mesh(trans_neg_x_mesh, color='red', pickable=True, name='trans_neg_x', render=False, opacity=0.8)
        self.manipulation_cylinders['trans_y'] = self.plotter.add_mesh(trans_y_mesh, color='green', pickable=True, name='trans_y', render=False, opacity=0.8)
        self.manipulation_cylinders['trans_neg_y'] = self.plotter.add_mesh(trans_neg_y_mesh, color='green', pickable=True, name='trans_neg_y', render=False, opacity=0.8)
        self.manipulation_cylinders['trans_z'] = self.plotter.add_mesh(trans_z_mesh, color='blue', pickable=True, name='trans_z', render=False, opacity=0.8)
        self.manipulation_cylinders['trans_neg_z'] = self.plotter.add_mesh(trans_neg_z_mesh, color='blue', pickable=True, name='trans_neg_z', render=False, opacity=0.8)
        
        rot_height = 2
        rot_radius = 100
        
        rot_x_mesh = pv.CylinderStructured(direction=(1, 0, 0), height=rot_height, radius=[rot_radius * 0.8, rot_radius])
        rot_y_mesh = pv.CylinderStructured(direction=(0, 1, 0), height=rot_height, radius=[rot_radius * 0.8, rot_radius])
        rot_z_mesh = pv.CylinderStructured(direction=(0, 0, 1), height=rot_height, radius=[rot_radius * 0.8, rot_radius])
        
        self.manipulation_cylinders['rot_x'] = self.plotter.add_mesh(rot_x_mesh, color='red', pickable=True, name='rot_x', render=False, opacity=0.2)
        self.manipulation_cylinders['rot_y'] = self.plotter.add_mesh(rot_y_mesh, color='green', pickable=True, name='rot_y', render=False, opacity=0.2)
        self.manipulation_cylinders['rot_z'] = self.plotter.add_mesh(rot_z_mesh, color='blue', pickable=True, name='rot_z', render=False, opacity=0.2)
    
    def update_manipulation_cylinders(self):
        initial_tool_matrix = pv.Transform().translate(self.manipulation_center_pos).matrix
        final_effector_matrix = self.transforms[-1]
        final_tool_matrix = final_effector_matrix @ initial_tool_matrix
        for actor in self.manipulation_cylinders.values():
            actor.user_matrix = final_tool_matrix
        self.plotter.render()
        
    def update_robot(self, q_angles_deg=None):
        if q_angles_deg is None:
            q_angles_deg = np.array(list(self.joint_angles.values()))
        
        self.joint_angles['Base'] = q_angles_deg[0]
        self.joint_angles['Shoulder'] = q_angles_deg[1]
        self.joint_angles['Elbow'] = q_angles_deg[2]
        self.joint_angles['Wrist 1'] = q_angles_deg[3]
        self.joint_angles['Wrist 2'] = q_angles_deg[4]
        
        for name, entry in self.entries.items():
            entry.setText(f"{self.joint_angles[name]:.2f}")
            
        self.transforms = []
        final_transform_base = pv.Transform().rotate_y(q_angles_deg[0]).matrix
        self.transforms.append(final_transform_base)
        final_transform_shoulder = final_transform_base @ pv.Transform().translate(link_pivots['Shoulder']).matrix @ pv.Transform().rotate_z(q_angles_deg[1]).matrix
        self.transforms.append(final_transform_shoulder)
        final_transform_elbow = final_transform_shoulder @ pv.Transform().translate(link_pivots['Elbow'] - link_pivots['Shoulder']).matrix @ pv.Transform().rotate_z(q_angles_deg[2]).matrix
        self.transforms.append(final_transform_elbow)
        final_transform_wrist1 = final_transform_elbow @ pv.Transform().translate(link_pivots['Wrist 1'] - link_pivots['Elbow']).matrix @ pv.Transform().rotate_z(q_angles_deg[3]).matrix
        self.transforms.append(final_transform_wrist1)
        final_transform_wrist2 = final_transform_wrist1 @ pv.Transform().translate(link_pivots['Wrist 2'] - link_pivots['Wrist 1']).matrix @ pv.Transform().rotate_y(q_angles_deg[4]).matrix
        self.transforms.append(final_transform_wrist2)
        
        self.robot_actors['Base'].user_matrix = final_transform_base
        self.robot_actors['Shoulder'].user_matrix = final_transform_shoulder
        self.robot_actors['Elbow'].user_matrix = final_transform_elbow
        self.robot_actors['Wrist 1'].user_matrix = final_transform_wrist1
        self.robot_actors['Wrist 2'].user_matrix = final_transform_wrist2
        
        self.effector_marker_actor = self.robot_actors['Wrist 2']
        
        self.update_manipulation_cylinders()
        self.plotter.render()
        
    def setup_robot_scene(self):
        self.plotter.background_color = 'white'
        base_cylinder = pv.Cylinder(radius=120, height=20, direction=(0, 1, 0))
        self.plotter.add_mesh(base_cylinder, color='blue', opacity=0.8, pickable=False)
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
            
        self.update_robot()

    def on_slider_change(self, value, name):
        pass

    def on_text_entry(self, name, entry):
        pass

    def calculate_and_plot_ellipsoid(self, jacobien, wrist2_transform_matrix, scale_factor=250):
        pass

if __name__ == '__main__':
    pygame.init()
    
    app = QtWidgets.QApplication(sys.argv)
    window = RobotApp()
    window.show()
    sys.exit(app.exec_())