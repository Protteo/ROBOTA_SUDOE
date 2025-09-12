#!/usr/bin/env python3
import rospy
import PyKDL as kdl
from sensor_msgs.msg import JointState
from urdf_parser_py.urdf import URDF
from kdl_parser_py.urdf import treeFromUrdfModel
import numpy as np

# Déclaration globale de la chaîne KDL et du solveur
kdl_chain = None
jac_solver = None

def joint_state_callback(msg):
    """
    Fonction de rappel pour le topic /joint_states.
    Calcule et affiche la Jacobienne à chaque mise à jour de l'état des joints.
    """
    if kdl_chain is None or jac_solver is None:
        return

    # Créer un tableau KDL à partir des positions des joints ROS
    joint_positions = kdl.JntArray(kdl_chain.getNrOfJoints())
    for i in range(kdl_chain.getNrOfJoints()):
        joint_positions[i] = msg.position[i]

    # Créer la matrice Jacobienne KDL
    jacobian_matrix = kdl.Jacobian(kdl_chain.getNrOfJoints())

    # Calculer la Jacobienne
    if jac_solver.JntToJac(joint_positions, jacobian_matrix) >= 0:
        rospy.loginfo("Matrice Jacobienne calculée :")
        # Convertir la matrice KDL en une matrice NumPy pour une meilleure lisibilité
        jac_np = np.array([[jacobian_matrix[i, j] for j in range(jacobian_matrix.columns())] for i in range(jacobian_matrix.rows())])
        rospy.loginfo("\n" + str(jac_np))
    else:
        rospy.logerr("Erreur lors du calcul de la Jacobienne.")

def main():
    global kdl_chain, jac_solver
    rospy.init_node('jacobian_calculator_py')

    # Charger le modèle URDF du robot à partir du serveur de paramètres ROS
    robot_description = rospy.get_param('robot_description')
    robot = URDF.from_xml_string(robot_description)

    # Créer la chaîne KDL de la base (base_link) à l'effecteur (tool0)
    # C'est la partie cruciale où KDL construit son modèle interne
    success, kdl_chain = treeFromUrdfModel(robot, 'base_link', 'tool0')
    if not success:
        rospy.logerr("Impossible de créer la chaîne KDL depuis le URDF.")
        return

    # Initialiser le solveur de Jacobienne
    jac_solver = kdl.ChainJntToJacSolver(kdl_chain)

    # S'abonner au topic des états des joints publié par Gazebo
    rospy.Subscriber('joint_states', JointState, joint_state_callback)

    rospy.spin()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass