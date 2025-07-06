#%%--------------------Importer les library------------------------------------
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#%%--------------------Ouvre le port série-------------------------------------
ser = serial.Serial("COM3",9600)

#%%--------------------Preparer la figure--------------------------------------
fig, ax = plt.subplots()
point, =ax.plot([], [], 'ro')
ax.set_xlim(-1,1)
ax.set_ylim(-1,1)
ax.set_xlabel("Latéral")
ax.set_ylabel("Vertical")
ax.grid(True)

def update(frame):
    line = ser.readline().decode().strip()
    try:
        x_str, y_str = line.split(",")
        x=float(x_str)
        y=float(y_str)
        point.set_data(x, y)
    except:
        pass
    return point,

ani = animation.FuncAnimation(fig, update, blit=True, interval=50)
plt.show()

#%%----------------------------Interprétation----------------------------------
if x >10:
    print("Tu le tiens en standard")
else:
    print("Tu le tiens en poignard")


