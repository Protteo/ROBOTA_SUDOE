import numpy as np

# Paramètres de Denavit-Hartenberg (DH)
a = np.array([0, 638, 502, 13, 0])
d = np.array([237.0, 0, 0, 0, -201.0])
alpha = np.array([90, 0, 0, 90, -90])

def calculate_transform_matrix(a_i, d_i, alpha_i, theta_i):
    """
    Calculates the transformation matrix for a single joint using DH parameters.
    """
    theta_rad = np.deg2rad(theta_i)
    alpha_rad = np.deg2rad(alpha_i)
    
    T = np.array([
        [np.cos(theta_rad), -np.sin(theta_rad) * np.cos(alpha_rad), np.sin(theta_rad) * np.sin(alpha_rad), a_i * np.cos(theta_rad)],
        [np.sin(theta_rad), np.cos(theta_rad) * np.cos(alpha_rad), -np.cos(theta_rad) * np.sin(alpha_rad), a_i * np.sin(theta_rad)],
        [0, np.sin(alpha_rad), np.cos(alpha_rad), d_i],
        [0, 0, 0, 1]
    ])
    return T

def calculate_forward_kinematics_matrix(q, a, d, alpha):
    """
    Calculates the final transformation matrix for the end-effector.
    """
    T_final = np.identity(4)
    for i in range(len(q)):
        T_link = calculate_transform_matrix(a[i], d[i], alpha[i], q[i])
        T_final = np.dot(T_final, T_link)
    return T_final

def calculate_jacobian(q, a, d, alpha):
    """
    Calculates the geometric Jacobian matrix.
    """
    n_dof = len(q)
    J = np.zeros((6, n_dof))
    
    T_list = [np.identity(4)]
    T_current = np.identity(4)
    for i in range(n_dof):
        T_current = np.dot(T_current, calculate_transform_matrix(a[i], d[i], alpha[i], q[i]))
        T_list.append(T_current)

    p_end_effector = T_list[-1][:3, 3]

    for i in range(n_dof):
        T_i_minus_1 = T_list[i]
        
        z_i_minus_1 = T_i_minus_1[:3, 2]
        p_i_minus_1 = T_i_minus_1[:3, 3]

        J[:3, i] = np.cross(z_i_minus_1, p_end_effector - p_i_minus_1)
        J[3:, i] = z_i_minus_1
        
    return J