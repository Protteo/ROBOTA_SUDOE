#!/usr/bin/env python3

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

def move_ur30_base_trajectory():
    """
    Ce script envoie une trajectoire en deux étapes pour faire pivoter le bras UR30.
    1. Retour à la position de départ (home).
    2. Rotation de la base de 90 degrés.
    """
    
    # Initialise le noeud ROS
    rospy.init_node('ur30_base_trajectory_controller', anonymous=True)

    # Crée un publisher pour envoyer les commandes de trajectoire
    pub = rospy.Publisher('/eff_joint_traj_controller/command', JointTrajectory, queue_size=10)

    # Attend que le publisher soit connecté au contrôleur
    rospy.sleep(1)

    # Crée le message de trajectoire
    traj_msg = JointTrajectory()
    
    # Définit le nom des joints
    traj_msg.joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']

    # --- Point 1 : Retour à la position de départ (home) ---
    point1 = JointTrajectoryPoint()
    point1.positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    point1.time_from_start = rospy.Duration(3.0)  # Temps pour atteindre la position home (3 secondes)
    
    # --- Point 2 : Rotation de la base de 90 degrés ---
    point2 = JointTrajectoryPoint()
    point2.positions = [0.0, -0.78, 1.57, -2.25, -1.57, 0.0]
    point2.time_from_start = rospy.Duration(6.0)  # Temps total pour le mouvement (3s + 3s = 6s)
    
    # Ajoute les points à la trajectoire
    traj_msg.points.append(point1)
    traj_msg.points.append(point2)
    
    rospy.loginfo("Début de la séquence : retour à home puis rotation de 90 degrés.")

    # Publie le message de trajectoire
    pub.publish(traj_msg)

    # Attend la fin du mouvement
    rospy.sleep(6.5)

    rospy.loginfo("Séquence terminée.")
    
if __name__ == '__main__':
    try:
        move_ur30_base_trajectory()
    except rospy.ROSInterruptException:
        pass