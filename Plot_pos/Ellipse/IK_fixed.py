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
            entry.returnPressed.connect(lambda n=name, e=entry: self.on_text_entry(n, e))
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
        
        # Map VTK actors to tool names for robust picking
        self.vtk_to_tool = {}
        self.active_tool_name = None
        try:
            for _name, _actor in self.manipulation_cylinders.items():
                _vtk_actor = getattr(_actor, "prop", _actor)
                self.vtk_to_tool[_vtk_actor] = _name
        except Exception:
            pass
        self.setup_robot_scene()
        
        self.plotter.iren.add_observer('LeftButtonPressEvent', self.on_mouse_down)
        self.plotter.iren.add_observer('LeftButtonReleaseEvent', self.on_mouse_up)
        self.plotter.iren.add_observer('MouseMoveEvent', self.on_mouse_move)

    def on_mouse_down(self, interactor, event):
        click_pos = interactor.GetEventPosition()
        
        picker = vtk.vtkPropPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, self.plotter.renderer)
        picked_vtk_actor = picker.GetActor()
        
        self.active_tool = None
        self.active_tool_name = None
        tool_name = self.vtk_to_tool.get(picked_vtk_actor)
        if tool_name:
            self.active_tool_name = tool_name
            self.active_tool = self.manipulation_cylinders.get(tool_name)
            self.is_dragging = True
            self.plotter.interactor.SetInteractorStyle(vtk.vtkInteractorStyleUser())
            self.mouse_pos_prev = np.array(interactor.GetEventPosition())
            if len(self.transforms) > 0:
                self.initial_effector_pos = self.transforms[-1][:3, 3]
        else:
            self.reset_interactor_style()

    def on_mouse_up(self, interactor, event):
        self.is_dragging = False
        self.active_tool = None
        self.active_tool_name = None
        self.mouse_pos_prev = None
        self.reset_interactor_style()

    def on_mouse_move(self, interactor, event):
        if not self.is_dragging or self.active_tool is None or interactor.GetControlKey() or interactor.GetShiftKey() or interactor.GetAltKey():
            return
        
        current_pos = np.array(interactor.GetEventPosition())
        effector_matrix = self.transforms[-1]
        
        effector_pos_global = effector_matrix[:3, 3]
        effector_rot_matrix = effector_matrix[:3, :3]
        
        manip_center_global = effector_pos_global + effector_rot_matrix @ self.manipulation_center_pos
        
        target_effector_matrix = np.eye(4)
        target_effector_matrix[:3, :3] = effector_rot_matrix
        
        mouse_prev_xy = np.array(self.mouse_pos_prev)
        mouse_curr_xy = np.array(current_pos)
        
        if self.active_tool_name and 'trans' in self.active_tool_name:
            # Use local axis of the effector (as RViz), transformed to world
            local_axis_map = {
                'trans_x': np.array([1, 0, 0]),
                'trans_y': np.array([0, 1, 0]),
                'trans_z': np.array([0, 0, 1]),
            }
            base_name = self.active_tool_name.replace('_neg', '')
            sign = -1.0 if '_neg' in self.active_tool_name else 1.0
            axis_dir = effector_rot_matrix @ local_axis_map[base_name]
            axis_dir = axis_dir / (np.linalg.norm(axis_dir) + 1e-12)
            axis_dir *= sign

            # mouse rays at previous and current positions
            x0, y0 = self.mouse_pos_prev
            x1, y1 = current_pos
            r0, u0 = self._mouse_ray(x0, y0)
            r1, u1 = self._mouse_ray(x1, y1)

            # Axis line: p = manip_center_global + t * axis_dir
            t_prev = self._closest_t_on_axis_from_ray(manip_center_global, axis_dir, r0, u0)
            t_curr = self._closest_t_on_axis_from_ray(manip_center_global, axis_dir, r1, u1)
            delta_t = t_curr - t_prev

            target_effector_matrix[:3, 3] = effector_pos_global + axis_dir * delta_t

        elif self.active_tool_name and 'rot' in self.active_tool_name:
            
            coord_ref = vtk.vtkCoordinate()
            coord_ref.SetCoordinateSystemToWorld()
            coord_ref.SetValue(manip_center_global)
            center_screen = np.array(coord_ref.GetComputedDisplayValue(self.plotter.renderer))[:2]
            
            vec_prev = mouse_prev_xy - center_screen
            vec_curr = mouse_curr_xy - center_screen
            
            vec_prev_3d = np.append(vec_prev, 0)
            vec_curr_3d = np.append(vec_curr, 0)
            
            norm_prev = np.linalg.norm(vec_prev_3d)
            norm_curr = np.linalg.norm(vec_curr_3d)
            
            if norm_prev < 1e-6 or norm_curr < 1e-6:
                self.mouse_pos_prev = current_pos
                return
            
            dot_product = np.dot(vec_prev_3d, vec_curr_3d)
            cross_product = np.cross(vec_prev_3d, vec_curr_3d)
            
            angle_rad = np.arctan2(np.linalg.norm(cross_product), dot_product)
            
            z_direction = np.sign(cross_product[2])
            
            local_axis_map = {
                'rot_x': np.array([1, 0, 0]),
                'rot_y': np.array([0, 1, 0]),
                'rot_z': np.array([0, 0, 1])
            }
            local_axis = local_axis_map.get(self.active_tool_name.replace('_neg', ''))
            
            global_axis = effector_rot_matrix @ local_axis
            
            rotation_delta = R.from_rotvec(global_axis * angle_rad * z_direction)
            
            current_rotation = R.from_matrix(effector_rot_matrix)
            new_rotation = rotation_delta * current_rotation
            
            target_effector_matrix[:3, :3] = new_rotation.as_matrix()
            
        self.mouse_pos_prev = current_pos
        self._solve_ik_iteratively(target_effector_matrix)
        self.update_manipulation_cylinders()

    def _mouse_ray(self, x, y):
        """Return (ray_origin, ray_dir) in world coordinates from screen coords."""
        p_near = np.array(self.plotter.renderer.DisplayToWorld(x, y, 0.0))[:3]
        p_far = np.array(self.plotter.renderer.DisplayToWorld(x, y, 1.0))[:3]
        d = p_far - p_near
        n = np.linalg.norm(d) + 1e-12
        return p_near, d / n

    def _closest_t_on_axis_from_ray(self, axis_point, axis_dir, ray_origin, ray_dir):
        """Closest point parameter t on the axis line to the given ray (origin+u*s)."""
        v = axis_dir
        u = ray_dir
        w0 = axis_point - ray_origin
        a = float(np.dot(v, v))
        b = float(np.dot(v, u))
        c = float(np.dot(u, u))
        d = float(np.dot(v, w0))
        e = float(np.dot(u, w0))
        denom = a * c - b * b
        if abs(denom) < 1e-9:
            # Fallback: intersect mouse ray with plane ⟂ axis through axis_point
            n = v / (np.linalg.norm(v) + 1e-12)
            denom2 = float(np.dot(ray_dir, n))
            if abs(denom2) < 1e-9:
                return 0.0
            t_ray = float(np.dot(axis_point - ray_origin, n) / denom2)
            p = ray_origin + t_ray * ray_dir
            return float(np.dot(p - axis_point, n))
        return float((b * e - c * d) / denom)

    def _solve_ik_iteratively(self, desired_effector_transform_matrix):
        max_iterations = 20
        epsilon_pos = 1.0
        epsilon_rot = 1.0

        q_angles_deg = np.array(list(self.joint_angles.values()))
        q_angles_rad = np.deg2rad(q_angles_deg)

        for i in range(max_iterations):
            self.update_robot(q_angles_deg)
            current_effector_transform = self.transforms[-1]
            
            current_pos = current_effector_transform[:3, 3]
            desired_pos = desired_effector_transform_matrix[:3, 3]

            current_rot_matrix = current_effector_transform[:3, :3]
            desired_rot_matrix = desired_effector_transform_matrix[:3, :3]
            
            delta_pos = desired_pos - current_pos
            R_err = desired_rot_matrix @ current_rot_matrix.T
            rot_vec = R.from_matrix(R_err).as_rotvec()
            
            dx_error = np.zeros(6)
            dx_error[:3] = delta_pos
            dx_error[3:] = rot_vec
            
            if np.linalg.norm(dx_error[:3]) < epsilon_pos and np.linalg.norm(np.rad2deg(dx_error[3:])) < epsilon_rot:
                break
                
            J = calculate_geometric_jacobian(self.transforms, current_pos)
            
            lambda_damping = 0.5 
            J_damped = J.T @ J + lambda_damping * np.eye(J.shape[1])
            J_pinv = np.linalg.inv(J_damped) @ J.T
            
            dq = J_pinv @ dx_error
            
            max_dq_deg = 5.0
            dq_norm = np.linalg.norm(np.rad2deg(dq))
            if dq_norm > max_dq_deg:
                dq = dq * (max_dq_deg / dq_norm)
            
            q_angles_deg += np.rad2deg(dq)
        
        self.update_robot(q_angles_deg)

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
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = RobotApp()
    window.show()
    sys.exit(app.exec_())