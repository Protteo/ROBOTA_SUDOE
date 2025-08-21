import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5 import QtWidgets, QtCore
import sys
import os
import numpy as np
from scipy.spatial.transform import Rotation as R
import time
import vtk

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

# Décalage de l'effecteur final
end_effector_offset = np.array([0.0, 150.0, -100.0])

def calculate_geometric_jacobian(transforms):
    J = np.zeros((6, 5))
    p_end_effector = transforms[-1][:3, 3]

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
        
        self.is_x_pressed = False
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
            entry.returnPressed.connect(lambda n=name, e=entry: self.on_text_entry(n, e))
            self.entries[name] = entry
            entry_layout.addWidget(label)
            entry_layout.addWidget(entry)
            control_layout.addLayout(entry_layout)

        self.manip_ellipsoid_actor = None
        self.effector_marker_actor = None 
        self.is_dragging = False
        self.mouse_pos_prev = None
        self.effector_marker_name = 'effector_marker'

        self.setup_robot_scene()
        
        self.plotter.iren.add_observer('KeyPressEvent', self.on_key_press)
        self.plotter.iren.add_observer('KeyReleaseEvent', self.on_key_release)
        self.plotter.iren.add_observer('LeftButtonPressEvent', self.on_mouse_down)
        self.plotter.iren.add_observer('LeftButtonReleaseEvent', self.on_mouse_up)
        self.plotter.iren.add_observer('MouseMoveEvent', self.on_mouse_move)

    def on_key_press(self, interactor, event):
        key = interactor.GetKeyCode()
        if key == 'x' or key == 'X':
            if not self.is_x_pressed:
                self.is_x_pressed = True
                self.last_key_press_time = time.time()

    def on_key_release(self, interactor, event):
        key = interactor.GetKeyCode()
        if key == 'x' or key == 'X':
            if time.time() - self.last_key_press_time > 0.1:
                self.is_x_pressed = False
            if self.is_dragging:
                self.is_dragging = False
                self.plotter.interactor.SetInteractorStyle(self.plotter_style)
                
    def on_mouse_down(self, interactor, event):
        pos = interactor.GetEventPosition()
        renderer = interactor.FindPokedRenderer(pos[0], pos[1])

        if renderer:
            picker = vtk.vtkPropPicker()
            picker.Pick(pos[0], pos[1], 0, renderer)
            actor = picker.GetActor()

            if actor:
                print(f"DEBUG: Actor sélectionné: {actor}")

                if self.is_x_pressed and actor == self.effector_marker_actor:
                    self.is_dragging = True
                    self.mouse_pos_prev = np.array(pos)
                    print("--- DÉBOGAGE : Commande 'x' + Clic gauche sur l'effecteur détectée. Début de la manipulation. ---")
                    
                    self.plotter.interactor.SetInteractorStyle(vtk.vtkInteractorStyleUser())
                    
    def on_mouse_up(self, interactor, event):
        if self.is_dragging:
            self.is_dragging = False
            self.plotter.interactor.SetInteractorStyle(self.plotter_style)

    def on_mouse_move(self, interactor, event):
        if self.is_dragging:
            pos_current = np.array(interactor.GetEventPosition())
            
            if np.array_equal(self.mouse_pos_prev, pos_current):
                return
            
            # Correction: pick_mouse_position() n'accepte pas l'argument 'pos'.
            # Il récupère la position de la souris directement de l'interactor.
            picked_point = self.plotter.pick_mouse_position()
            
            if picked_point is not None:
                current_end_effector_pos = self.effector_marker_actor.user_matrix[:3, 3]
                
                # Calcule le vecteur de déplacement de l'effecteur
                delta_pos = picked_point - current_end_effector_pos
                
                self.solve_inverse_kinematics(delta_pos)
            
    def solve_inverse_kinematics(self, delta_pos, alpha_step=1.0):
        q_angles_deg = np.array(list(self.joint_angles.values()))
        
        jacobien = calculate_geometric_jacobian(self.transforms)
        
        J_v = jacobien[:3, :]
        
        try:
            pinv_J = np.linalg.pinv(J_v)
            delta_q = pinv_J @ delta_pos
            
            delta_q_norm = np.linalg.norm(delta_q)
            if delta_q_norm > 0:
                delta_q = delta_q / delta_q_norm * alpha_step
            
            delta_q[0] = 0.0

            new_q_deg = q_angles_deg + np.rad2deg(delta_q)
            
            names = list(self.joint_angles.keys())
            for i in range(len(names)):
                self.joint_angles[names[i]] = new_q_deg[i]
                self.entries[names[i]].setText(f"{new_q_deg[i]:.2f}")
                
            self.update_robot()
            
        except np.linalg.LinAlgError:
            pass 

    def update_robot(self, q_angles_deg=None):
        if q_angles_deg is None:
            q_angles_deg = np.array(list(self.joint_angles.values()))

        self.joint_angles['Base'] = q_angles_deg[0]
        self.joint_angles['Shoulder'] = q_angles_deg[1]
        self.joint_angles['Elbow'] = q_angles_deg[2]
        self.joint_angles['Wrist 1'] = q_angles_deg[3]
        self.joint_angles['Wrist 2'] = q_angles_deg[4]

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

        effector_transform = final_transform_wrist2 @ pv.Transform().translate(end_effector_offset).matrix
        self.effector_marker_actor.user_matrix = effector_transform

        try:
            jacobien = calculate_geometric_jacobian(self.transforms)
            if self.manip_ellipsoid_actor:
                self.plotter.remove_actor(self.manip_ellipsoid_actor)
        except Exception as e:
            pass
        
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

        effector_sphere = pv.Sphere(radius=25, phi_resolution=20, theta_resolution=20)
        self.effector_marker_actor = self.plotter.add_mesh(effector_sphere, color='blue', opacity=0.8, name=self.effector_marker_name)

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
            pass

    def calculate_and_plot_ellipsoid(self, jacobien, wrist2_transform_matrix, scale_factor=250):
        Jv = jacobien[:3, :]
        
        try:
            U, s, Vt = np.linalg.svd(Jv)
            if np.isclose(s[0], 0, atol=1e-6):
                if self.manip_ellipsoid_actor:
                    self.plotter.remove_actor(self.manip_ellipsoid_actor)
                return
            s_scaled = s / s[0] * scale_factor
            if self.manip_ellipsoid_actor:
                self.plotter.remove_actor(self.manip_ellipsoid_actor)

            ellipsoid_mesh = pv.Sphere(radius=1.0, phi_resolution=30, theta_resolution=30)
            ellipsoid_mesh.scale(s_scaled, inplace=True)
            
            ellipsoid_transform = wrist2_transform_matrix @ pv.Transform().translate(end_effector_offset).matrix
            ellipsoid_mesh.transform(ellipsoid_transform, inplace=True)
            self.manip_ellipsoid_actor = self.plotter.add_mesh(ellipsoid_mesh, color='red', opacity=0.5, style='wireframe', pickable=False)
            
        except np.linalg.LinAlgError:
            if self.manip_ellipsoid_actor:
                self.plotter.remove_actor(self.manip_ellipsoid_actor)
        except Exception as e:
            pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = RobotApp()
    window.show()
    sys.exit(app.exec_())