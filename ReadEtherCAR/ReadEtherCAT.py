import pysoem

master = pysoem.Master()

master.open('Carte Ethernet')

if master.config_init() > 0:
    device_foo = master.slaves[0]
    device_bar = master.slaves[1]
else:
    print('no device found')

master.close()
#%%
from scapy.all import sniff

# Fonction de callback pour traiter chaque paquet capturé
def process_packet(packet):
    print(packet.summary())

# Capture de paquets sur une interface réseau (exemple : 'Wi-Fi')
sniff(iface="Ethernet 2", prn=process_packet, count=10)
