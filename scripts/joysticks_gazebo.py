#!/usr/bin/env python

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
import time

# Variables globales
current_joint_state = None
current_joystick_values = [0.0] * 6
pub = None

def joint_state_callback(data):
    """
    Callback pour le topic /joint_states. Met à jour l'état des joints.
    """
    global current_joint_state
    current_joint_state = data

def joystick_callback(data):
    """
    Callback pour le topic du joystick.
    """
    global current_joystick_values
    if len(data.data) >= 6:
        current_joystick_values = list(data.data[:6])

def main():
    global pub
    rospy.init_node('joysticks_gazebo', anonymous=True)

    # Création du publisher et des subscribers
    # Le topic /joint_group_vel_controller/command attend une JointTrajectory pour des commandes en vitesse
    pub = rospy.Publisher('/joint_group_vel_controller/command', JointTrajectory, queue_size=10)
    rospy.Subscriber("/joint_states", JointState, joint_state_callback)
    rospy.Subscriber("/joysticks_publisher", Float64MultiArray, joystick_callback)

    rospy.loginfo("Contrôleur de joints démarré. En attente des données des joints et du joystick...")
    
    # Attendre les données initiales
    try:
        rospy.wait_for_message("/joint_states", JointState, timeout=5.0)
        rospy.loginfo("Données de joints initiales reçues.")
    except rospy.ROSException as e:
        rospy.logerr("L'initialisation a échoué: %s. Vérifiez que le driver du robot est lancé.", e)
        return

    rate = rospy.Rate(10)  # Boucle de contrôle à 10 Hz

    while not rospy.is_shutdown():
        if current_joint_state is None:
            rospy.logwarn("En attente de l'état actuel des joints...")
            rate.sleep()
            continue
        
        # Créer le message de trajectoire
        traj_msg = JointTrajectory()
        traj_msg.joint_names = current_joint_state.name
        
        # Créer le point de trajectoire
        point = JointTrajectoryPoint()
        
        # Utiliser les valeurs du joystick comme des vitesses de joint
        # La valeur de 0.5 est un facteur d'échelle, ajuste-le pour la sensibilité
        point.velocities = [val * 0.5 for val in current_joystick_values]
        point.time_from_start = rospy.Duration(0.1)
        
        # Ajouter le point et publier
        traj_msg.points.append(point)
        pub.publish(traj_msg)
        
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass