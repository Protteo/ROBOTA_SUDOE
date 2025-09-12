#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Joy

class ContinuousJoyRemapper:
    def __init__(self):
        # Initialiser le noeud ROS
        rospy.init_node('IK_joysticks_publisher', anonymous=True)
        
        self.joy_publisher = rospy.Publisher('/IK_joy_publisher', Joy, queue_size=10)
        
        # Le subscriber sur le topic /joy1 de votre joystick
        rospy.Subscriber('/joy1', Joy, self.joy_callback)

        # Variables pour stocker les données du joystick
        self.joy_axes = [0.0] * 8
        self.joy_buttons = [0] * 11
        
        rospy.loginfo("Remapper continu a démarré, s'abonne à /joy1 et publie sur /IK_joy_publisher.")

    def joy_callback(self, joy_msg):
        """
        Met à jour les variables d'instance avec les données brutes du joystick.
        """
        # Mise à jour des données du joystick lorsque le callback est appelé
        self.joy_axes = joy_msg.axes
        self.joy_buttons = joy_msg.buttons

    def run(self):
        # Définir la fréquence de publication (par exemple, 50 Hz)
        rate = rospy.Rate(250) 
        
        while not rospy.is_shutdown():
            # Créer un nouveau message Joy pour les données mappées
            mapped_joy_msg = Joy()
            mapped_joy_msg.header.stamp = rospy.Time.now()
            
            # Appliquer le facteur de vélocité
            velocity_factor = 0.75

            # --- Mappage des axes ---
            # Vos règles de mappage sont appliquées ici
            # Remarque : Les indices des axes et des boutons dépendent de votre joystick.
            # Les axes et boutons sont réinitialisés à zéro pour les valeurs non mappées.
            
            # Initialiser les tableaux avec des valeurs par défaut
            mapped_axes = [0.0] * 6
            mapped_buttons = [0] * 6
            
            # Exemple de mappage basé sur votre logique :
            # Vous devrez ajuster les indices des axes et des boutons si nécessaire
            
            # Mappage de la translation X/Y/Z
            mapped_axes[0] = self.joy_axes[0] * velocity_factor    # X
            mapped_axes[1] = (self.joy_axes[1]-0.56) * velocity_factor    # Y
            
            # Mappage de la rotation Roll/Pitch/Yaw
            mapped_axes[3] = self.joy_axes[4] * velocity_factor    # Roll
            mapped_axes[4] = self.joy_axes[5] * velocity_factor    # Pitch
            
            # Gérer la translation Z avec les boutons
            if self.joy_buttons[0] == 1: # Bouton 0
                mapped_axes[2] = velocity_factor
            if self.joy_buttons[1] == 1: # Bouton 1
                mapped_axes[2] = -velocity_factor
            
            # Gérer la rotation Yaw avec les boutons
            if self.joy_buttons[2] == 1: # Bouton 2
                mapped_axes[5] = velocity_factor
            if self.joy_buttons[3] == 1: # Bouton 3
                mapped_axes[5] = -velocity_factor

            # Appliquer la "zone morte" pour l'axe Y (si la valeur est trop petite, elle est mise à zéro)
            if abs(mapped_axes[1]) < 0.2 * velocity_factor:
                mapped_axes[1] = 0.0
            
            mapped_buttons[5]=self.joy_buttons[5]

            # Attribuer les valeurs mappées au message
            mapped_joy_msg.axes = mapped_axes
            mapped_joy_msg.buttons = mapped_buttons

            # Publier le message mappé
            self.joy_publisher.publish(mapped_joy_msg)
            
            # Attendre jusqu'à la prochaine itération
            rate.sleep()

if __name__ == '__main__':
    try:
        remapper = ContinuousJoyRemapper()
        remapper.run()
    except rospy.ROSInterruptException:
        pass