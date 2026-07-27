import trimesh

target_faces = 50000  # Change this as needed

for i in range(6):
    path = f"/home/dexter/Documents/GitHub/tactile-ball-robot/ball-gym/src/mujoco_tactile_ball/assets/objects/z{i}_surface.stl"

    mesh = trimesh.load(path)

    print(f"z{i}: {len(mesh.faces)} -> ", end="")

    # Only simplify if necessary
    if len(mesh.faces) > target_faces:
        mesh = mesh.simplify_quadric_decimation(face_count=target_faces)

    print(len(mesh.faces))

    mesh.export(path)