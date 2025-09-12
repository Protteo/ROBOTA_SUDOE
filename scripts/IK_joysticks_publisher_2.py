#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class CartesianJoyController:
    def __init__(self):
        rospy.init_node('IK_joysticks_publisher_2')

        # Publisher vers le topic de commande du contrôleur
        self.twist_pub = rospy.Publisher('/twist_controller/command', Twist, queue_size=1)
        
        # Subscriber à votre topic de joystick
        rospy.Subscriber('/IK_joy_publisher', Joy, self.joy_callback)

        self.twist_msg = Twist()
        self.rate = rospy.Rate(50)  # 50 Hz, une bonne fréquence pour le contrôle en temps réel

    def joy_callback(self, data):
        # Mappage des axes du joystick aux vitesses de l'effecteur final
        self.twist_msg.linear.x = data.axes[0]  # Vitesse linéaire en X
        self.twist_msg.linear.y = data.axes[1]  # Vitesse linéaire en Y
        self.twist_msg.linear.z = data.axes[2]  # Vitesse linéaire en Z

        self.twist_msg.angular.x = data.axes[3] # Vitesse angulaire autour de X (Roll)
        self.twist_msg.angular.y = data.axes[4] # Vitesse angulaire autour de Y (Pitch)
        self.twist_msg.angular.z = data.axes[5] # Vitesse angulaire autour de Z (Yaw)

    def run(self):
        while not rospy.is_shutdown():
            self.twist_pub.publish(self.twist_msg)
            self.rate.sleep()

if __name__ == '__main__':
    try:
        controller = CartesianJoyController()
        controller.run()
    except rospy.ROSInterruptException:
        pass