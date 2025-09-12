#!/usr/bin/env python3
import rospy
import PyKDL as kdl
from sensor_msgs.msg import Joy, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from urdf_parser_py.urdf import URDF
from kdl_parser_py.urdf import treeFromUrdfModel
import numpy as np

# Globals
kdl_chain = None
jac_solver = None
last_joint_state = None            # stocke le dernier JointState reçu
target_positions = None            # cible intégrée (gelée quand joystick neutre)
v_cartesian = np.zeros(6)         # [vx, vy, vz, wx, wy, wz]
gain_linear = 0.25
gain_angular = 0.25
prev_button_state=False

JOINT_NAMES = [
    'shoulder_pan_joint',
    'shoulder_lift_joint',
    'elbow_joint',
    'wrist_1_joint',
    'wrist_2_joint',
    'wrist_3_joint'
]

def joy_callback(msg):
    global v_cartesian, gain_linear, gain_angular, prev_button_state

    # --- Détection front montant sur bouton 6 (index 5) ---
    if msg.buttons[5] == 1 and not prev_button_state:  
        # Toggle entre faible et fort gain
        if abs(gain_linear - 0.08) < 1e-6:  
            gain_linear = 0.3
            gain_angular = 0.3
            rospy.loginfo("Gains augmentés : gain_linear=%.2f, gain_angular=%.2f", gain_linear, gain_angular)
        else:
            gain_linear = 0.08
            gain_angular = 0.08
            rospy.loginfo("Gains réduits : gain_linear=%.2f, gain_angular=%.2f", gain_linear, gain_angular)

    # Toujours mettre à jour après pour mémoriser l’état
    prev_button_state = (msg.buttons[5] == 1)


    # --- Conversion joystick → vitesse cartésienne ---
    v_cartesian = np.array([
        msg.axes[0] * gain_linear,
        -msg.axes[1] * gain_linear,
        msg.axes[2] * gain_linear * 0.5,
        -msg.axes[4] * gain_angular,
        -msg.axes[3] * gain_angular,
        msg.axes[5] * gain_angular
    ])
  

def joint_state_callback(msg):
    global last_joint_state
    last_joint_state = msg
    rospy.loginfo_throttle(2, "JointState reçu: %s", msg.position)

def main():
    global kdl_chain, jac_solver, last_joint_state, target_positions, v_cartesian
    rospy.init_node('ur5e_joystick_controller')

    # robot_description
    robot_description = rospy.get_param('robot_description', None)
    if robot_description is None:
        rospy.logerr("Paramètre 'robot_description' introuvable.")
        return

    robot = URDF.from_xml_string(robot_description)
    ok, tree = treeFromUrdfModel(robot)
    if not ok:
        rospy.logerr("Impossible de créer le KDL Tree depuis l'URDF.")
        return

    try:
        kdl_chain = tree.getChain('base_link', 'tool0')  # adapter si besoin
    except Exception as e:
        rospy.logerr("Erreur extraction KDL chain: %s", e)
        return

    if kdl_chain.getNrOfJoints() == 0:
        rospy.logerr("La chaîne KDL contient 0 articulations.")
        return

    jac_solver = kdl.ChainJntToJacSolver(kdl_chain)
    rospy.loginfo("KDL Chain initialized: %d joints", kdl_chain.getNrOfJoints())

    rospy.Subscriber('/IK_joy_publisher', Joy, joy_callback)
    rospy.Subscriber('/joint_states', JointState, joint_state_callback)
    # pub = rospy.Publisher('/eff_joint_traj_controller/command', JointTrajectory, queue_size=1) #Dans gazebo
    pub = rospy.Publisher('/scaled_pos_joint_traj_controller/command', JointTrajectory, queue_size=1) #ur5e


    rate_hz = 100
    rate = rospy.Rate(rate_hz)
    delta_t = 1.0 / float(rate_hz)   # integration timestep cohérent avec la boucle

    vel_threshold = 1e-6             # seuil pour considérer q_dot = 0
    resync_threshold = 0.5           # si target diverge trop de la mesure, resync (rad)

    while not rospy.is_shutdown():
        try:
            if last_joint_state is None:
                rate.sleep()
                continue

            n_joints = kdl_chain.getNrOfJoints()
            # construire positions_ordered dans l'ordre JOINT_NAMES à partir de last_joint_state
            positions_ordered = np.zeros(n_joints)
            name_to_idx = {name: idx for idx, name in enumerate(last_joint_state.name)}
            for i, jn in enumerate(JOINT_NAMES):
                if jn in name_to_idx:
                    positions_ordered[i] = last_joint_state.position[name_to_idx[jn]]
                else:
                    rospy.logwarn_throttle(5, "Joint '%s' absent de /joint_states ; utilisation de 0.", jn)
                    positions_ordered[i] = 0.0

            # initialisation de target_positions si première fois
            if target_positions is None:
                target_positions = positions_ordered.copy()

            # calcul de la Jacobienne (au point mesuré)
            joint_positions_kdl = kdl.JntArray(n_joints)
            for i, pos in enumerate(positions_ordered):
                joint_positions_kdl[i] = pos

            jacobian_matrix = kdl.Jacobian(n_joints)
            jac_solver.JntToJac(joint_positions_kdl, jacobian_matrix)

            rows, cols = jacobian_matrix.rows(), jacobian_matrix.columns()
            jac_np = np.zeros((rows, cols))
            for i in range(rows):
                for j in range(cols):
                    jac_np[i, j] = jacobian_matrix[i, j]

            if jac_np.size == 0:
                rospy.logwarn("Jacobian vide -> pas de calcul q_dot.")
                rate.sleep()
                continue

            # pseudo-inverse
            q_dot_full = np.linalg.pinv(jac_np).dot(v_cartesian)

            # s'assurer de la taille (on prend les premières n joints si nécessaire)
            q_dot_ordered = np.zeros(len(JOINT_NAMES))
            L = min(len(q_dot_full), len(q_dot_ordered))
            q_dot_ordered[:L] = q_dot_full[:L]

            # DEBUG
            rospy.logdebug("q_dot: %s", q_dot_ordered.tolist())

            # Si au moins une composante significative -> intégration, sinon freeze target_positions
            if np.any(np.abs(q_dot_ordered) > vel_threshold):
                target_positions = target_positions + q_dot_ordered * delta_t


            # Sécurité : si target diverge trop de la position mesurée, resynchroniser
            if np.max(np.abs(target_positions - positions_ordered)) > resync_threshold:
                rospy.logwarn("Target diverge de la mesure (>%.2f rad). Resynchronisation.", resync_threshold)
                target_positions = positions_ordered.copy()

            # Publication (positions + velocities + accelerations de même taille)
            jt_msg = JointTrajectory()
            jt_msg.joint_names = JOINT_NAMES
            point = JointTrajectoryPoint()
            point.positions = target_positions.tolist()
            point.velocities = q_dot_ordered.tolist()
            point.accelerations = [0.0] * len(JOINT_NAMES)
            point.time_from_start = rospy.Duration(delta_t)
            jt_msg.points.append(point)
            pub.publish(jt_msg)

        except Exception as e:
            rospy.logerr("Erreur dans la boucle de contrôle : %s", e)

        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
