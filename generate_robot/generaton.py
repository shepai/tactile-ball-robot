import numpy as np
import xml.etree.ElementTree as ET

def generate_dome(R=1.0, n_layers=20, n_total=300,
                  tip_layer_density=2.0, min_pts=6,
                  remove_top_layers=1):

    points = []
    layer_indices = []   # stores indices of points per layer
    actual_layer_counts = []

    t = np.linspace(0, 1, n_layers)

    z_vals = R * (np.sin(t * np.pi / 2) ** (1 / tip_layer_density))

    circumferences = 2 * np.pi * np.sqrt(np.maximum(R**2 - z_vals**2, 0))
    weights = circumferences + 1.0
    weights = weights / weights.sum()

    layer_counts = (weights * n_total).astype(int)

    current_idx = 0

    for i, (z, n_pts) in enumerate(zip(z_vals, layer_counts)):
        r = np.sqrt(max(R**2 - z**2, 0))

        layer_start_idx = current_idx

        # apex / degenerate layer handling
        if r < 1e-8:
            points.append((0.0, 0.0, R))
            layer_indices.append([current_idx])
            actual_layer_counts.append(1)
            current_idx += 1
            continue

        n_pts = max(min_pts, n_pts)

        theta = np.linspace(0, 2*np.pi, n_pts, endpoint=False)

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        for xi, yi in zip(x, y):
            points.append((xi, yi, z))

        layer_end_idx = current_idx + n_pts
        layer_indices.append(list(range(layer_start_idx, layer_end_idx)))

        actual_layer_counts.append(n_pts)
        current_idx = layer_end_idx

    # -------------------------
    # REMOVE TOP LAYERS HERE
    # -------------------------
    if remove_top_layers > 0:
        top_layers = layer_indices[-remove_top_layers:]

        flat_remove_idx = set(idx for layer in top_layers for idx in layer)

        points = [
            p for i, p in enumerate(points)
            if i not in flat_remove_idx
        ]
        actual_layer_counts = actual_layer_counts[:-remove_top_layers]

    return np.array(points) / 10.0, actual_layer_counts
def generate_xml(name,points, num,stiff=300,damp=20):
    if sum(num) != len(points):
        raise ValueError(
            f"Topology mismatch: sum(num)={sum(num)} vs len(points)={len(points)}"
        )
    xml = f"""<mujoco model="{name}">
     <option integrator="implicitfast" timestep="0.001"/> 
     <asset>
         <material name="black_mesh_mat_{name}" rgba="0.05 0.05 0.05 1" shininess="0.1"/>
    </asset>
       <worldbody>
        <body name="flexible_structure_{name}" pos="0 0 0">
            <inertial pos="0 0 0" mass="0.1" diaginertia="0.0005 0.0005 0.0005"/>
            """
    xml += f"""
        <body name="cylinder_mount_{name}" pos="0 0 -0.01">
            <geom type="cylinder"
                size="0.107 0.0025"
                mass="0.07"
                rgba="0 0 0 0" group="1"/>
        </body>
        

    """
    layers = []
    idx = 0
    for n in num:
        layers.append(list(range(idx, idx + n)))
        idx += n
    # -------------------------
    # create nodes
    # -------------------------
    allnames=""
    for i in range(len(points)):
        point = points[i]
        inner_pos = point * -0.2
        xml += f"""
        <body name="node_{i}_{name}" pos="{point[0]} {point[1]} {point[2]}">
            <joint type="slide" axis="1 0 0" name="j_c{i}_x_{name}" stiffness="{stiff}" damping="{damp}"/>
            <joint type="slide" axis="0 1 0" name="j_c{i}_y_{name}" stiffness="{stiff}" damping="{damp}"/>
            <joint type="slide" axis="0 0 1" name="j_c{i}_z_{name}" stiffness="{stiff}" damping="{damp}"/>
            <geom type="sphere" size="0.001" rgba="1 1 1 0" mass="0.01" condim="3" contype="1" conaffinity="1"/>
            <geom pos="{inner_pos[0]} {inner_pos[1]} {inner_pos[2]}" type="sphere" size="0.002" rgba="1 1 1 1" 
            
                group="2" 
                contype="0" 
                conaffinity="0" 
                mass="0" 
                density="0"/>
            <site name="s_c{i}_{name}" pos="0 0 0" size="0.002"/>
        </body>
        """
        allnames+= f"node_{i}_{name} "
    xml += """
        </body>
</worldbody>
    <tendon>
    """
    
    for i, layer in enumerate(layers):
        n = len(layer)

        for j in range(n):
            if n != 1:
                a = layer[j]
                b = layer[(j + 1) % n]
                xml += f"""
                <spatial width="0.002" name="t_h_{i}_{j}_{name}" 
                        damping="2"
                        solreflimit="0.008 1" solimplimit="0.95 0.99 0.001">
                    <site site="s_c{a}_{name}"/>
                    <site site="s_c{b}_{name}"/>
                </spatial>"""

    for i in range(len(layers) - 1):
        curr = layers[i]
        nxt = layers[i + 1]

        n_curr = len(curr)
        n_nxt = len(nxt)

        for j, a in enumerate(curr):
            k = int(j * n_nxt / n_curr)
            k = min(max(k, 0), n_nxt - 1)
            b = nxt[k]
            if a == b:
                continue

            xml += f"""
            <spatial width="0.002" name="t_v_{i}_{j}_{name}" solreflimit="0.008 1" solimplimit="0.95 0.99 0.001">
                <site site="s_c{a}_{name}"/>
                <site site="s_c{b}_{name}"/>
            </spatial>"""
    center = layers[0][0]
    spoke_stiff = 1500
    spoke_damp = 15
    for i in range(len(layers)):
        curr = layers[i]

        for j in range(0, len(curr), 10):  
            a = curr[j]

            if a == center:
                continue

            xml += f"""
            <spatial width="0.002"
                    rgba="0 0 0 0"
                    name="t_spoke_{i}_{j}_{name}"
                    stiffness="{spoke_stiff}"
                    damping="{spoke_damp}"
                    solreflimit="0.005 1"
                    solimplimit="0.9 0.95 0.001">
                <site site="s_c{center}_{name}"/>
                <site site="s_c{a}_{name}"/>
            </spatial>"""
    elements = []
    for i in range(len(layers) - 1):
        curr = layers[i]
        nxt = layers[i + 1]
        n_curr = len(curr)
        n_nxt = len(nxt)

        if n_curr == 1: # Apex layer fanning out
            apex = curr[0]
            for j in range(n_nxt):
                elements.append(f"{apex} {nxt[j]} {nxt[(j + 1) % n_nxt]}")
        else: # Standard concentric rings stitching together
            for j in range(n_curr):
                c1, c2 = curr[j], curr[(j + 1) % n_curr]
                k1 = min(max(int(j * n_nxt / n_curr), 0), n_nxt - 1)
                k2 = min(max(int(((j + 1) % n_curr) * n_nxt / n_curr), 0), n_nxt - 1)
                
                # Draw the structural triangle grids between the layers
                elements.append(f"{c1} {nxt[k1]} {c2}")
                if k1 != k2:
                    elements.append(f"{c2} {nxt[k1]} {nxt[k2]}")

    element_str = "   ".join(elements)
    body_str = " ".join([f"node_{i}_{name}" for i in range(len(points))])
    vertex_str = "   ".join(["0 0 0" for _ in range(len(points))])
    xml += f"""
    </tendon>
    <deformable>
    <flex name="black_skin_{name}" 
              material="black_mesh_mat_{name}" 
              dim="2"
              body="{body_str}"
              vertex="{vertex_str}"
              element="{element_str}"/>
    </deformable>
    """
    xml += "<equality>\n"
    for i in range(num[0]):
        xml += f'  <joint joint1="j_c{i}_x_{name}" polycoef="0 1 0 0 0"/>\n'
        xml += f'  <joint joint1="j_c{i}_y_{name}" polycoef="0 1 0 0 0"/>\n'
        xml += f'  <joint joint1="j_c{i}_z_{name}" polycoef="0 1 0 0 0"/>\n'
    xml += """</equality>\n
    </mujoco>
    """
    
    return xml

def seperate(folder):
    tree = ET.parse(folder+"generated.xml")
    root = tree.getroot()

    for tag in ["asset", "worldbody", "tendon", "actuator", "sensor","deformable","equality"]:
        elem = root.find(tag)

        if elem is not None:
            ET.ElementTree(elem).write(
                f"{folder}/{tag}.xml",
                encoding="utf-8",
                xml_declaration=False,
            )
def generate_body():
    points,layers=generate_dome(R=1.0, n_layers=16, n_total=150,
                  tip_layer_density=2.0, min_pts=6)
    left_xml=generate_xml("leftwheel",points,layers,stiff=150,damp=60)
    right_xml=generate_xml("rightwheel",points,layers,stiff=150,damp=60)
    with open("/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/robot/left_wheel/generated.xml","w") as file:
        file.write(left_xml)
    with open("/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/robot/right_wheel/generated.xml","w") as file:
        file.write(right_xml)
    seperate("/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/robot/left_wheel/")
    seperate("/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/robot/right_wheel/")

if __name__=="__main__":
    generate_body()