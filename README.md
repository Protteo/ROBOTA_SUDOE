# Description  
<ins>**Plot_Pos**</ins> : Inside, there is a file with every data got from expériences <ins>**wrench_camera_data**</ins>.   
- **Plot_pos.py** enable to plot 4 Windows to get different pieces of information. You get real time values for the 6 sensors, a histogram about the values' frequency for each sensor, a 3D representation to have the force center and a color map to see which sensor is the most used.
- **Acquisition_data_handle_video.py** : enable to turn csv data from expereinces into a 30s video where we can see the evolution of the color mapping.
- <ins>**Ellipse**</ins> : This file contains code (**Ellipse.py**) to manipulate a UR30 simulation through direct kinematic with pyvista. The purpose is to show the manipulability ellipse of this arm. We can control it with cursors or with an input window.
- **3Dhandle.py** : This code shows a 3D representation of the handle with the six sensors on it. Furthermore, It shows through a colour gradient the way the sensors are used.
- **3DHandle_video.py** : This code do the same thing that **3Dhandle.py**, but it gets data from csv files got from experiments to show teh way the sensors were used for 30 seconds.  
  
<ins>**PPorPS**</ins> : This file is related to the neural network and the guessing on the way we are holding the knife thaanks to the 6 tactile sensors put on it : in standard mode or in reverse mode.
The csv files are related to different experiences to train the neural network on several situations : when the robotic arm doesn't move or when there is only two classes to guess for instance. 
**PositionNN.py** and **PositionNN_Teensy.py** have the same purpose, but **PositionNN.py** is for the flexible handle and **PositionNN_Teensy.py** is for the Teensy cardboard.
To create a neural network, you have to launch this code three times :
- One time to create a csv file to get training data about all the classes you need;
- One time to train the model according to the classes you created;
- One last time to predict the classes in real time with new data.
  
<ins>**Tactile_sensor**</ins> : Arduino code for Teensy 4.1 to get the sensors' values as : value1,value2,value3,value4,value5,value6.  

<ins>**scripts**</ins> : This file contain every Python code to use the robotic arms UR, with MoveIt and without it, through direct kinematic and inverse kinematic. You can also use them with gazebo simulation and manipulate it with a joystick. Don't forget to put this file in the package you are using. 
To use them, please install this repository and to put the script file in the **ur_gazebo** package :  
```
git clone https://github.com/ros-industrial/universal_robot.git
```

The useful codes are :  
- **joysticks_publisher.py** : publishes the joystick data in the good topic for direct kinematic
- **move_arm_node.py** : to put the arm in a pose by setting the position of each joint
- **IK_position_moveit.py** : to put the arm in a pose by setting the coordinates through inverse kinematic and MoveIt
- **IK_joysticks_publisher.py** : to map the joystick for inverse kinematic
- **IK_control.py** : to control the arm through inverse kinematic with the joystick
- **gripper_joy.py** : to open/close the gripper with the joystick  
  
**Commands** :  
To launch the drivers :  
```
roslaunch ur_robot_driver ur5e_bringup.launch robot_ip:=192.168.56.2 kinematics_config:="/home/titouan/joy_ws/src/universal_robot/ur5e_moveit_config/config/ur5e_calibration.yaml"
```
To find the name of the joystick :
```
ls -l /dev/input/
```
To get the joystick data :  
``` 
rosrun joy joy_node _dev:=/dev/input/js1 joy:=/joy1 __name:=joystick_one
```
To map the joystick for inverse kinematic :  
```
rosrun ur_gazebo IK_joysticks_publisher.py
```
To map the joystick for direct kinematic :
```
rosrun ur_gazebo joysticks_publisher.py
```
To open/close the gripper with the joystick :
```
rosrun ur_gazebo gripper_joy.py
```
To control the arm through inverse kinematic :
```
rosrun ur_gazebo IK_control.py
```

**For gazebo with MoveIt and Rviz :**  
To launch the simulation :
```
roslaunch ur_gazebo ur5e_bringup.launch
```
To start MoveIt planification :
```
roslaunch ur5e_moveit_config moveit_planning_execution.launch sim:=true
```
To open Rviz :
```
roslaunch ur5e_moveit_config moveit_rviz.launch
```

**If you have any question** :  
matteo.proverbio@sigma-clermont.fr
