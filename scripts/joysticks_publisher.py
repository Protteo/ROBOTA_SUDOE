#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Joy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState

class JoystickToMoveItPublisher:
    def __init__(self):
        rospy.init_node('joystick_moveit_publisher', anonymous=True)
        
        # Publisher for the MoveIt! joint position command topic
        self.traj_pub = rospy.Publisher('/scaled_pos_joint_traj_controller/command', JointTrajectory, queue_size=1)
        # self.traj_pub = rospy.Publisher('/eff_joint_traj_controller/command', JointTrajectory, queue_size=1)
        

        # Subscriber for raw joystick data
        rospy.Subscriber('/joy1', Joy, self.joy_callback)

        # Subscriber for the robot's current joint state
        rospy.Subscriber('/joint_states', JointState, self.joint_state_callback)
        
        # Joystick data
        self.joy_axes = [0.0] * 8
        self.joy_buttons = [0] * 11
        self.current_joint_positions = [0.0] * 6
        
        # Set the publishing rate
        self.rate = rospy.Rate(250)  # 250 Hz for smooth motion

    def joint_state_callback(self, data):
        self.current_joint_positions = data.position

    def joy_callback(self, data):
        # Callback function simply updates the class variables
        self.joy_axes = data.axes
        self.joy_buttons = data.buttons

    def run(self):
        rospy.loginfo("Contrôleur démarré. Attente des données du joystick...")
        # Define delta_t once, based on the fixed rate
        delta_t = 2
        
        while not rospy.is_shutdown():
            if len(self.joy_axes) < 6 or len(self.joy_buttons) < 4:
                self.rate.sleep()
                continue
            
            # Joint speed factor
            joint_speed_factor = 0.5
            
            # Map joystick axes to joint velocities
            joint_velocities = [
                0,
                self.joy_axes[0] * joint_speed_factor,
                (self.joy_axes[1]-0.56) * joint_speed_factor,
                self.joy_axes[4] * joint_speed_factor,
                self.joy_axes[5] * joint_speed_factor,
                0,
            ]

            # Button logic
            if self.joy_buttons[0] == 1:
                joint_velocities[0] = joint_speed_factor
            if self.joy_buttons[1] == 1:
                joint_velocities[0] = -joint_speed_factor
            if self.joy_buttons[2] == 1:
                joint_velocities[5] = joint_speed_factor
            if self.joy_buttons[3] == 1:
                joint_velocities[5] = -joint_speed_factor
            
            if abs(joint_velocities[2])<0.2:
                joint_velocities[2]=0

            # Calculate new target positions
            target_positions = [
                self.current_joint_positions[i] + joint_velocities[i] * delta_t for i in range(6)
            ]

            # Create and publish trajectory message
            traj_msg = JointTrajectory()
            traj_msg.joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                                    'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
            
            point = JointTrajectoryPoint()
            point.positions = target_positions
            point.velocities = joint_velocities
            point.time_from_start = rospy.Duration(delta_t)
            
            traj_msg.points.append(point)
            self.traj_pub.publish(traj_msg)
            
            # Sleep to maintain the fixed rate
            self.rate.sleep()

if __name__ == '__main__':
    try:
        publisher = JoystickToMoveItPublisher()
        publisher.run()
    except rospy.ROSInterruptException:
        pass