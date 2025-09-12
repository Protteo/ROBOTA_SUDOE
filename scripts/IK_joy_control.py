#!/usr/bin/env python3

import rospy
import sys
from geometry_msgs.msg import Pose
from sensor_msgs.msg import Joy
from moveit_commander import RobotCommander, MoveGroupCommander
from moveit_commander import roscpp_initialize, roscpp_shutdown
from tf.transformations import quaternion_from_euler, euler_from_quaternion

class JoystickCartesianControl:
    def __init__(self):
        roscpp_initialize(sys.argv)
        rospy.init_node('IK_joy_control', anonymous=True)

        self.robot = RobotCommander()
        self.move_group = MoveGroupCommander("manipulator")
        
        self.joy_axes = None
        
        rospy.Subscriber("/IK_joy_publisher", Joy, self.joy_callback)
        rospy.loginfo("Contrôle du bras par joystick démarré. Attente de données du joystick...")
        
    def joy_callback(self, data):
        self.joy_axes = data.axes

    def control_loop(self):
        rate = rospy.Rate(30)  # 30 Hz

        linear_scale = 0.5   # m/s
        angular_scale = 0.5  # rad/s
        time_step = 0.1      # incrément de temps

        while not rospy.is_shutdown():
            if self.joy_axes is not None:
                # Pose actuelle
                current_pose = self.move_group.get_current_pose().pose

                # Vitesse linéaire
                linear_velocity = [
                    self.joy_axes[0] * linear_scale,
                    self.joy_axes[1] * linear_scale,
                    self.joy_axes[2] * linear_scale
                ]

                # Vitesse angulaire
                angular_velocity = [
                    self.joy_axes[3] * angular_scale,
                    self.joy_axes[4] * angular_scale,
                    self.joy_axes[5] * angular_scale
                ]

                # Nouvelle position
                target_pose = Pose()
                target_pose.position.x = current_pose.position.x + linear_velocity[0] * time_step
                target_pose.position.y = current_pose.position.y + linear_velocity[1] * time_step
                target_pose.position.z = current_pose.position.z + linear_velocity[2] * time_step

                # Nouvelle orientation
                current_roll, current_pitch, current_yaw = euler_from_quaternion([
                    current_pose.orientation.x,
                    current_pose.orientation.y,
                    current_pose.orientation.z,
                    current_pose.orientation.w
                ])
                new_roll = current_roll + angular_velocity[0] * time_step
                new_pitch = current_pitch + angular_velocity[1] * time_step
                new_yaw = current_yaw + angular_velocity[2] * time_step
                
                q_new = quaternion_from_euler(new_roll, new_pitch, new_yaw)
                target_pose.orientation.x = q_new[0]
                target_pose.orientation.y = q_new[1]
                target_pose.orientation.z = q_new[2]
                target_pose.orientation.w = q_new[3]

                # Waypoints : départ + arrivée
                waypoints = [current_pose, target_pose]

                # Génération trajectoire cartésienne
                (plan, fraction) = self.move_group.compute_cartesian_path(
                    waypoints,
                    0.001,   # pas = 1 mm
                    False
                )  

                # ✅ Si ça marche : exécution
                if fraction > 0.0:
                    self.move_group.execute(plan, wait=False)

                # ❌ Sinon, plan de secours répétitif
                else:
                    rospy.logwarn("Aucun plan trouvé. Activation du plan de secours (+Z).")
                    success = False
                    rescue_pose = current_pose

                    while not success and not rospy.is_shutdown():
                        # Monter petit à petit en Z
                        rescue_pose = Pose()
                        rescue_pose.position.x = current_pose.position.x
                        rescue_pose.position.y = current_pose.position.y
                        rescue_pose.position.z = current_pose.position.z + 0.01  # +1 cm
                        rescue_pose.orientation = current_pose.orientation

                        rescue_waypoints = [current_pose, rescue_pose]
                        (rescue_plan, rescue_fraction) = self.move_group.compute_cartesian_path(
                            rescue_waypoints,
                            0.001,
                            False
                        )

                        if rescue_fraction > 0.0:
                            rospy.loginfo("Mouvement de secours réussi (+Z).")
                            self.move_group.execute(rescue_plan, wait=True)
                            success = True
                        else:
                            rospy.logwarn("Échec du secours, nouvelle tentative +Z...")
                            current_pose.position.z += 0.01  # on monte encore
                            rospy.sleep(0.1)  # petite pause pour éviter de saturer

            rate.sleep()

if __name__ == '__main__':
    try:
        controller = JoystickCartesianControl()
        controller.control_loop()
    except rospy.ROSInterruptException:
        roscpp_shutdown()
