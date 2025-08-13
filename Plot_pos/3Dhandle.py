import pyvista as pv

# ====== CONFIGURATION ======
fichier_stl = r"C:\Users\matte\OneDrive\Documents\Scolaire\Sigma\2A\Stage\ROBOTA SUDOE\ROBOTA SUDOE 2025 BRIANCON-PROVERBIO\CAD\STL\Handle\Manche_couteau.STL"

# Dimensions des capteurs (x_length, y_length, z_length) pour chaque capteur
dimensions_capteurs = [
    (60, 20, 1),
    (60, 20, 1),
    (60, 20, 1),
    (60, 20, 1),
    (60, 1, 20),  # Capteur dans plan XZ
    (60, 1, 20)   # Capteur dans plan XZ
]

# Coordonnées des capteurs (x, y, z)
positions_capteurs = [
    (60, 33, 31),
    (60, 33, 7),
    (125, 33, 31),
    (125, 33, 7),
    (125, 45, 18.8),
    (60, 45, 18.8)
]
# ===========================

# Charger le manche
mesh = pv.read(fichier_stl)

# Création du plotter
plotter = pv.Plotter()
plotter.add_mesh(mesh, color="lightgray")
plotter.add_axes()   # Affiche le repère
plotter.show_grid()  # Affiche la grille

# Ajouter les capteurs avec leurs dimensions et positions individuelles
for i, (pos, dim) in enumerate(zip(positions_capteurs, dimensions_capteurs), start=1):
    capteur = pv.Cube(center=pos,
                      x_length=dim[0],
                      y_length=dim[1],
                      z_length=dim[2])
    plotter.add_mesh(capteur, color="red")
    print(f"Capteur {i} placé à {pos} avec dimensions {dim}")

# Afficher le tout
plotter.show()
