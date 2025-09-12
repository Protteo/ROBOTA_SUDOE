#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Joy
from ur_msgs.srv import SetIO

class GripperControlNodeROS1:
    def __init__(self):
        rospy.init_node('gripper_joy', anonymous=True)

        self.gripper_state = False
        self.last_button_state = 0

        self.joy_subscriber = rospy.Subscriber('/joy1', Joy, self.joy_callback)

        rospy.wait_for_service('/ur_hardware_interface/set_io')
        self.set_io = rospy.ServiceProxy('/ur_hardware_interface/set_io', SetIO)

        rospy.loginfo("Gripper control node prêt (écoute /joy1)")

    def joy_callback(self, msg):
        button_index = 4
        current_button_state = msg.buttons[button_index]

        if current_button_state == 1 and self.last_button_state == 0:
            self.gripper_state = not self.gripper_state
            self.publish_gripper_command(self.gripper_state)
            rospy.loginfo(f"Bouton pressé. Gripper -> {self.gripper_state}")

        self.last_button_state = current_button_state

    def publish_gripper_command(self, state):
        fun = 1      # digital out
        pin = 1      # sortie 1
        state_val = 1.0 if state else 0.0

        try:
            resp = self.set_io(fun, pin, state_val)
            rospy.loginfo("Commande envoyée, succès: %s", resp.success)
        except rospy.ServiceException as e:
            rospy.logerr("Erreur appel SetIO: %s", e)

if __name__ == '__main__':
    try:
        node = GripperControlNodeROS1()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
