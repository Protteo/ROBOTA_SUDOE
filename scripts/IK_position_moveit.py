#!/usr/bin/env python3

import rospy
import sys
from geometry_msgs.msg import PoseStamped
from moveit_commander import RobotCommander, MoveGroupCommander, PlanningSceneInterface
from moveit_commander import roscpp_initialize, roscpp_shutdown
from moveit_msgs.msg import DisplayTrajectory
from tf.transformations import quaternion_from_euler

def move_to_pose(x, y, z, roll, pitch, yaw):
    """
    Planifie et exécute un mouvement pour que l'effecteur atteigne une pose donnée.
    """
    try:
        # Initialisation de moveit_commander et du noeud ROS
        roscpp_initialize(sys.argv)
        rospy.init_node('IK_position_moveit', anonymous=True)

        # Création des objets MoveIt
        robot = RobotCommander()
        scene = PlanningSceneInterface()
        group_name = "manipulator"
        move_group = MoveGroupCommander(group_name)
        
        # Définir le nom de la trame de référence pour la pose
        move_group.set_pose_reference_frame("base_link")

        # Créer l'objet PoseStamped pour la cible
        pose_goal = PoseStamped()
        pose_goal.header.frame_id = "base_link"
        pose_goal.header.stamp = rospy.Time.now()

        # Remplir les coordonnées de position
        pose_goal.pose.position.x = x
        pose_goal.pose.position.y = y
        pose_goal.pose.position.z = z

        # Convertir les angles d'Euler en Quaternions pour l'orientation
        q = quaternion_from_euler(roll, pitch, yaw)
        pose_goal.pose.orientation.x = q[0]
        pose_goal.pose.orientation.y = q[1]
        pose_goal.pose.orientation.z = q[2]
        pose_goal.pose.orientation.w = q[3]
        print(q)

        # Définir la cible de pose
        move_group.set_pose_target(pose_goal)

        # Planifier et exécuter le mouvement avec la fonction go()
        rospy.loginfo("Planification et exécution du mouvement...")
        success = move_group.go(wait=True)
        
        if success:
            rospy.loginfo("Mouvement réussi.")
        else:
            rospy.logerr("Le plan de mouvement a échoué. Assurez-vous que les coordonnées de la cible sont atteignables.")
        
        # Arrêter le mouvement et nettoyer la cible
        move_group.stop()
        move_group.clear_pose_targets()

    except rospy.ROSInterruptException:
        pass
    finally:
        # Arrêter le gestionnaire C++ de ROS
        roscpp_shutdown()

if __name__ == '__main__':
    # Définir les coordonnées de la cible
    # Attention: ces valeurs doivent être physiquement atteignables par l'UR5e
    x_target = 0.3
    y_target = 0.3
    z_target = 0.6
    roll_target = -0.78     # Orientation de l'effecteur en radians
    pitch_target = 0.78  # 90 degrés, pour que l'effecteur pointe vers le bas
    yaw_target = 0.78
    
    try:
        move_to_pose(x_target, y_target, z_target, roll_target, pitch_target, yaw_target)
    except Exception as e:
        rospy.logerr("Une erreur s'est produite : %s" % e)