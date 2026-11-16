"""
Script to generate sample projects:
1. SCARA 4-DOF Assembly Robot
2. Dual-Arm Precision Workcell
"""

import json
from pathlib import Path

projects_dir = Path("projects")
projects_dir.mkdir(parents=True, exist_ok=True)

# 1. SCARA Robot
scara_dir = projects_dir / "scara_assembly_robot"
scara_dir.mkdir(parents=True, exist_ok=True)
(scara_dir / "experiments").mkdir(exist_ok=True)
(scara_dir / "trajectories").mkdir(exist_ok=True)

scara_manifest = {
    "version": "1.1.0",
    "metadata": {
        "id": "scara_assembly_robot",
        "name": "High-Speed SCARA 4-DOF Assembly Manipulator",
        "description": "High-throughput 4-axis SCARA manipulator (RRPR kinematics) engineered for electronic component insertion and rapid pick-and-place packaging.",
        "created_at": "2026-11-16T22:00:00Z",
        "updated_at": "2026-11-16T22:00:00Z",
        "author": "MonkeyBots Robotics Systems",
        "robot_type": "SCARA Manipulator",
        "tags": ["scara", "assembly", "pick-and-place", "high-speed"]
    },
    "robot": {
        "model_file": "robot.mjcf",
        "urdf_file": "robot.urdf",
        "dof": 4,
        "end_effector_site": "tool_tip",
        "default_qpos": [0.0, 0.0, 0.0, 0.0]
    },
    "physics": {
        "timestep": 0.001,
        "integrator": "RK4",
        "gravity": [0.0, 0.0, -9.81],
        "collision_tolerance": 0.0005,
        "solver": "Newton",
        "iterations": 60
    },
    "controllers": {
        "default_mode": "position",
        "gains": [
            {"joint": "scara_joint_1", "kp": 600.0, "ki": 1.5, "kd": 45.0, "max_torque": 200.0},
            {"joint": "scara_joint_2", "kp": 450.0, "ki": 1.0, "kd": 30.0, "max_torque": 150.0},
            {"joint": "scara_joint_z", "kp": 800.0, "ki": 2.0, "kd": 60.0, "max_torque": 250.0},
            {"joint": "scara_joint_yaw", "kp": 120.0, "ki": 0.2, "kd": 10.0, "max_torque": 40.0}
        ]
    },
    "trajectories": [],
    "geometry_assets": []
}

(scara_dir / "project.json").write_text(json.dumps(scara_manifest, indent=2), encoding="utf-8")

scara_mjcf = """<mujoco model="MonkeyBots_SCARA_4DOF">
  <compiler angle="radian" coordinate="local" autolimits="true"/>
  <option timestep="0.001" gravity="0 0 -9.81" integrator="RK4"/>
  <asset>
    <material name="metal_gray" rgba="0.75 0.78 0.82 1.0" roughness="0.3" metallic="0.7"/>
    <material name="accent_blue" rgba="0.12 0.53 0.90 1.0" roughness="0.2"/>
    <material name="dark_chassis" rgba="0.18 0.20 0.25 1.0"/>
    <material name="steel" rgba="0.85 0.85 0.88 1.0"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1" rgba="0.1 0.12 0.16 1.0"/>
    <body name="base_column" pos="0 0 0">
      <geom name="base_geom" type="cylinder" size="0.12 0.35" pos="0 0 0.35" material="dark_chassis"/>
      <body name="scara_link_1" pos="0 0 0.70">
        <joint name="scara_joint_1" type="hinge" axis="0 0 1" range="-2.617 2.617" damping="1.5" frictionloss="0.5"/>
        <geom name="link1_geom" type="capsule" size="0.06" fromto="0 0 0 0.35 0 0" material="accent_blue"/>
        <body name="scara_link_2" pos="0.35 0 0">
          <joint name="scara_joint_2" type="hinge" axis="0 0 1" range="-2.79 2.79" damping="1.2" frictionloss="0.4"/>
          <geom name="link2_geom" type="capsule" size="0.05" fromto="0 0 0 0.30 0 0" material="metal_gray"/>
          <body name="quill_shaft" pos="0.30 0 0">
            <joint name="scara_joint_z" type="slide" axis="0 0 1" range="-0.20 0.05" damping="2.5" frictionloss="0.8"/>
            <geom name="quill_geom" type="cylinder" size="0.018 0.18" pos="0 0 -0.05" material="steel"/>
            <body name="wrist_roll" pos="0 0 -0.15">
              <joint name="scara_joint_yaw" type="hinge" axis="0 0 1" range="-6.28 6.28" damping="0.4"/>
              <geom name="wrist_geom" type="cylinder" size="0.025 0.02" material="dark_chassis"/>
              <site name="tool_tip" pos="0 0 -0.02" size="0.01" rgba="1 0 0 1"/>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="act_j1" joint="scara_joint_1" ctrlrange="-200 200"/>
    <motor name="act_j2" joint="scara_joint_2" ctrlrange="-150 150"/>
    <motor name="act_jz" joint="scara_joint_z" ctrlrange="-250 250"/>
    <motor name="act_jyaw" joint="scara_joint_yaw" ctrlrange="-40 40"/>
  </actuator>
</mujoco>
"""
(scara_dir / "robot.mjcf").write_text(scara_mjcf, encoding="utf-8")

scara_urdf = """<?xml version="1.0"?>
<robot name="MonkeyBots_SCARA_4DOF">
  <link name="base_column">
    <visual>
      <origin xyz="0 0 0.35" rpy="0 0 0"/>
      <geometry><cylinder radius="0.12" length="0.70"/></geometry>
    </visual>
  </link>
  <joint name="scara_joint_1" type="revolute">
    <parent link="base_column"/>
    <child link="scara_link_1"/>
    <origin xyz="0 0 0.70" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-2.617" upper="2.617" effort="200" velocity="4.0"/>
  </joint>
  <link name="scara_link_1">
    <visual>
      <origin xyz="0.175 0 0" rpy="0 1.570796 0"/>
      <geometry><cylinder radius="0.06" length="0.35"/></geometry>
    </visual>
  </link>
  <joint name="scara_joint_2" type="revolute">
    <parent link="scara_link_1"/>
    <child link="scara_link_2"/>
    <origin xyz="0.35 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-2.79" upper="2.79" effort="150" velocity="4.5"/>
  </joint>
  <link name="scara_link_2">
    <visual>
      <origin xyz="0.15 0 0" rpy="0 1.570796 0"/>
      <geometry><cylinder radius="0.05" length="0.30"/></geometry>
    </visual>
  </link>
  <joint name="scara_joint_z" type="prismatic">
    <parent link="scara_link_2"/>
    <child link="quill_shaft"/>
    <origin xyz="0.30 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-0.20" upper="0.05" effort="250" velocity="1.5"/>
  </joint>
  <link name="quill_shaft">
    <visual>
      <origin xyz="0 0 -0.05" rpy="0 0 0"/>
      <geometry><cylinder radius="0.018" length="0.36"/></geometry>
    </visual>
  </link>
  <joint name="scara_joint_yaw" type="revolute">
    <parent link="quill_shaft"/>
    <child link="wrist_roll"/>
    <origin xyz="0 0 -0.15" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-6.28" upper="6.28" effort="40" velocity="8.0"/>
  </joint>
  <link name="wrist_roll">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><cylinder radius="0.025" length="0.04"/></geometry>
    </visual>
  </link>
</robot>
"""
(scara_dir / "robot.urdf").write_text(scara_urdf, encoding="utf-8")

# 2. Dual-Arm Precision Workcell
dual_dir = projects_dir / "precision_dual_arm_workcell"
dual_dir.mkdir(parents=True, exist_ok=True)
(dual_dir / "experiments").mkdir(exist_ok=True)
(dual_dir / "trajectories").mkdir(exist_ok=True)

dual_manifest = {
    "version": "1.1.0",
    "metadata": {
        "id": "precision_dual_arm_workcell",
        "name": "Cooperative Dual-Arm Bimanual Workcell",
        "description": "Coordinated bimanual workcell consisting of twin synchronized 6-DOF industrial arms mounted opposite a precision fixture table for cooperative object handling.",
        "created_at": "2026-11-16T22:10:00Z",
        "updated_at": "2026-11-16T22:10:00Z",
        "author": "MonkeyBots Robotics Systems",
        "robot_type": "Dual-Arm Bimanual System",
        "tags": ["bimanual", "dual-arm", "cooperative", "workcell"]
    },
    "robot": {
        "model_file": "robot.mjcf",
        "urdf_file": "robot.urdf",
        "dof": 12,
        "end_effector_site": "right_flange",
        "default_qpos": [0.0, -0.6, 1.2, 0.0, 0.6, 0.0, 0.0, -0.6, 1.2, 0.0, 0.6, 0.0]
    },
    "physics": {
        "timestep": 0.002,
        "integrator": "RK4",
        "gravity": [0.0, 0.0, -9.81],
        "collision_tolerance": 0.001,
        "solver": "Newton",
        "iterations": 50
    },
    "controllers": {
        "default_mode": "position",
        "gains": [
            {"joint": "left_j1", "kp": 350.0, "ki": 0.5, "kd": 25.0, "max_torque": 150.0},
            {"joint": "left_j2", "kp": 450.0, "ki": 1.0, "kd": 40.0, "max_torque": 150.0},
            {"joint": "left_j3", "kp": 300.0, "ki": 0.5, "kd": 20.0, "max_torque": 150.0},
            {"joint": "left_j4", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0},
            {"joint": "left_j5", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0},
            {"joint": "left_j6", "kp": 80.0,  "ki": 0.05, "kd": 5.0,  "max_torque": 28.0},
            {"joint": "right_j1", "kp": 350.0, "ki": 0.5, "kd": 25.0, "max_torque": 150.0},
            {"joint": "right_j2", "kp": 450.0, "ki": 1.0, "kd": 40.0, "max_torque": 150.0},
            {"joint": "right_j3", "kp": 300.0, "ki": 0.5, "kd": 20.0, "max_torque": 150.0},
            {"joint": "right_j4", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0},
            {"joint": "right_j5", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0},
            {"joint": "right_j6", "kp": 80.0,  "ki": 0.05, "kd": 5.0,  "max_torque": 28.0}
        ]
    },
    "trajectories": [],
    "geometry_assets": []
}

(dual_dir / "project.json").write_text(json.dumps(dual_manifest, indent=2), encoding="utf-8")

dual_mjcf = """<mujoco model="MonkeyBots_DualArm_Workcell">
  <compiler angle="radian" coordinate="local" autolimits="true"/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="RK4"/>
  <asset>
    <material name="aluminum" rgba="0.82 0.84 0.87 1.0" roughness="0.4"/>
    <material name="left_arm_mat" rgba="0.15 0.55 0.95 1.0"/>
    <material name="right_arm_mat" rgba="0.95 0.45 0.15 1.0"/>
    <material name="worktable_mat" rgba="0.22 0.25 0.30 1.0"/>
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="4 4 0.1" rgba="0.1 0.12 0.15 1.0"/>
    <geom name="central_table" type="box" size="0.4 0.6 0.35" pos="0 0 0.35" material="worktable_mat"/>
    
    <!-- Left Manipulator (-0.6m in X) -->
    <body name="left_base" pos="-0.6 0 0.35">
      <geom name="left_base_geom" type="cylinder" size="0.08 0.1" pos="0 0 0.1" material="left_arm_mat"/>
      <body name="left_link1" pos="0 0 0.2">
        <joint name="left_j1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
        <geom name="l_l1" type="cylinder" size="0.05 0.1" pos="0 0 0.1" material="aluminum"/>
        <body name="left_link2" pos="0 0 0.2">
          <joint name="left_j2" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
          <geom name="l_l2" type="capsule" size="0.04" fromto="0 0 0 0 0 0.3" material="left_arm_mat"/>
          <body name="left_link3" pos="0 0 0.3">
            <joint name="left_j3" type="hinge" axis="0 1 0" range="-2.5 2.5"/>
            <geom name="l_l3" type="capsule" size="0.035" fromto="0 0 0 0 0 0.25" material="aluminum"/>
            <body name="left_link4" pos="0 0 0.25">
              <joint name="left_j4" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
              <geom name="l_l4" type="cylinder" size="0.03 0.05" material="left_arm_mat"/>
              <body name="left_link5" pos="0 0 0.08">
                <joint name="left_j5" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                <geom name="l_l5" type="cylinder" size="0.025 0.04" material="aluminum"/>
                <body name="left_link6" pos="0 0 0.06">
                  <joint name="left_j6" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
                  <geom name="l_l6" type="cylinder" size="0.025 0.02" material="left_arm_mat"/>
                  <site name="left_flange" pos="0 0 0.02" size="0.01"/>
                </body>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>

    <!-- Right Manipulator (+0.6m in X) -->
    <body name="right_base" pos="0.6 0 0.35">
      <geom name="right_base_geom" type="cylinder" size="0.08 0.1" pos="0 0 0.1" material="right_arm_mat"/>
      <body name="right_link1" pos="0 0 0.2">
        <joint name="right_j1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
        <geom name="r_l1" type="cylinder" size="0.05 0.1" pos="0 0 0.1" material="aluminum"/>
        <body name="right_link2" pos="0 0 0.2">
          <joint name="right_j2" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
          <geom name="r_l2" type="capsule" size="0.04" fromto="0 0 0 0 0 0.3" material="right_arm_mat"/>
          <body name="right_link3" pos="0 0 0.3">
            <joint name="right_j3" type="hinge" axis="0 1 0" range="-2.5 2.5"/>
            <geom name="r_l3" type="capsule" size="0.035" fromto="0 0 0 0 0 0.25" material="aluminum"/>
            <body name="right_link4" pos="0 0 0.25">
              <joint name="right_j4" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
              <geom name="r_l4" type="cylinder" size="0.03 0.05" material="right_arm_mat"/>
              <body name="right_link5" pos="0 0 0.08">
                <joint name="right_j5" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
                <geom name="r_l5" type="cylinder" size="0.025 0.04" material="aluminum"/>
                <body name="right_link6" pos="0 0 0.06">
                  <joint name="right_j6" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
                  <geom name="r_l6" type="cylinder" size="0.025 0.02" material="right_arm_mat"/>
                  <site name="right_flange" pos="0 0 0.02" size="0.01"/>
                </body>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="act_l1" joint="left_j1" ctrlrange="-150 150"/>
    <motor name="act_l2" joint="left_j2" ctrlrange="-150 150"/>
    <motor name="act_l3" joint="left_j3" ctrlrange="-150 150"/>
    <motor name="act_l4" joint="left_j4" ctrlrange="-28 28"/>
    <motor name="act_l5" joint="left_j5" ctrlrange="-28 28"/>
    <motor name="act_l6" joint="left_j6" ctrlrange="-28 28"/>
    <motor name="act_r1" joint="right_j1" ctrlrange="-150 150"/>
    <motor name="act_r2" joint="right_j2" ctrlrange="-150 150"/>
    <motor name="act_r3" joint="right_j3" ctrlrange="-150 150"/>
    <motor name="act_r4" joint="right_j4" ctrlrange="-28 28"/>
    <motor name="act_r5" joint="right_j5" ctrlrange="-28 28"/>
    <motor name="act_r6" joint="right_j6" ctrlrange="-28 28"/>
  </actuator>
</mujoco>
"""
(dual_dir / "robot.mjcf").write_text(dual_mjcf, encoding="utf-8")

dual_urdf = """<?xml version="1.0"?>
<robot name="MonkeyBots_DualArm_Workcell">
  <link name="world"/>
  <joint name="table_joint" type="fixed">
    <parent link="world"/>
    <child link="central_table"/>
    <origin xyz="0 0 0.35" rpy="0 0 0"/>
  </joint>
  <link name="central_table">
    <visual>
      <geometry><box size="0.8 1.2 0.7"/></geometry>
    </visual>
  </link>
  <joint name="left_base_joint" type="fixed">
    <parent link="world"/>
    <child link="left_base"/>
    <origin xyz="-0.6 0 0.35" rpy="0 0 0"/>
  </joint>
  <link name="left_base"/>
  <joint name="right_base_joint" type="fixed">
    <parent link="world"/>
    <child link="right_base"/>
    <origin xyz="0.6 0 0.35" rpy="0 0 0"/>
  </joint>
  <link name="right_base"/>
</robot>
"""
(dual_dir / "robot.urdf").write_text(dual_urdf, encoding="utf-8")

print("Successfully generated SCARA and Dual-Arm sample projects.")
