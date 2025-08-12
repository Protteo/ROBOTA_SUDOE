# Description  
<ins>**Plot_Pos**</ins> : Inside, there is a file with every data got from expériences <ins>**wrench_camera_data**</ins>.   
- **Plot_pos.py** enable to plot 4 Windows to get different pieces of information. You get real time values for the 6 sensors, a histogram about the values' frequency for each sensor, a 3D representation to have the force center and a color map to see which sensor is the most used.
- **Acquisition_data_handle_video.py** : enable to turn csv data from expereinces into a 30s video where we can see the evolution of the color mapping.  
  
<ins>**PPorPS**</ins> : This file is related to the neural network and the guessing on the way we are holding the knife : in standard mode or in reverse mode.
The csv files are related to different experiences to train the neural network on several situations : when the robotic arm doesn't move or when there is only two classes to guess for instance. 
**PositionNN.py** and **PositionNN_Teensy.py** have the same purpose, but **PositionNN.py** is for the flexible handle and **PositionNN_Teensy.py** is for the Teensy cardboard.
To create a neural network, you have to launch this code three times :
- One time to create a csv file to get training data about all the classes you need;
- One time to train the model according to the classes you created;
- One last time to predict the classes in real time with new data.
  
<ins>**Tactile_sensor**</ins> : Arduino code for Teensy 4.1 to get the sensors' values as : value1,value2,value3,value4,value5,value6.  

**If you have any question** :  
matteo.proverbio@sigma-clermont.fr

