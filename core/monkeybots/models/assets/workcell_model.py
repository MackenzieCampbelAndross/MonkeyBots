"""
MonkeyBots Workcell & Gripper Model Generator
Defines the complete industrial workcell:
- 6-DOF industrial manipulator
- Actuated 2-finger parallel jaw gripper with high-friction silicone pads (mu = 1.2)
- Heavy granite workbench (pos=[0.45, 0.0, 0.1], top surface at z = 0.20 m)
- Free-floating manipulable object (cube mass = 0.15 kg, mu = 1.2, freejoint)
- Cylindrical obstacle pillar (pos=[0.35, 0.35, 0.30], r = 0.04 m, h = 0.60 m)
"""

from typing import Tuple
from pathlib import Path


def generate_workcell_mjcf(
    object_mass: float = 0.15,
    object_pos: Tuple[float, float, float] = (0.45, 0.0, 0.225),
    friction_coefficient: float = 1.2,
) -> str:
    """Generates native DeepMind MuJoCo XML (MJCF) representing the full robotic workcell."""
    ox, oy, oz = object_pos
    mjcf_xml = f"""<?xml version="1.0" ?>
<mujoco model="MonkeyBots_Workcell_6DOF_Gripper">
  <compiler angle="radian" coordinate="local" inertiafromgeom="false"/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicit" cone="elliptic"/>

  <default>
    <joint damping="0.5" armature="0.02"/>
    <geom friction="{friction_coefficient} 0.01 0.0001" margin="0.001" solref="0.004 1" solimp="0.95 0.99 0.001"/>
  </default>

  <visual>
    <headlight ambient="0.4 0.4 0.4" diffuse="0.8 0.8 0.8" specular="0.1 0.1 0.1"/>
  </visual>

  <worldbody>
    <light directional="true" diffuse="0.8 0.8 0.8" pos="0 0 3" dir="0 0 -1"/>
    
    <!-- Floor -->
    <geom name="floor" type="plane" size="5 5 0.1" rgba="0.12 0.15 0.22 1.0" friction="0.8 0.1 0.1"/>

    <!-- Heavy Industrial Workbench Surface (Top surface at z = 0.20 m) -->
    <body name="work_table" pos="0.45 0.0 0.10">
      <geom name="table_geom" type="box" size="0.25 0.30 0.10" rgba="0.22 0.26 0.34 1.0" friction="0.9 0.01 0.0001"/>
    </body>

    <!-- Obstacle Pillar (for collision avoidance and impact testing) -->
    <body name="obstacle_pillar" pos="0.30 0.35 0.30">
      <geom name="obstacle_geom" type="cylinder" size="0.04 0.30" rgba="0.85 0.25 0.25 0.9" friction="0.8 0.1 0.1"/>
    </body>

    <!-- Free Manipulable Object (Cube: mass 0.15 kg, half-size 0.025 m) -->
    <body name="manipulable_box" pos="{ox} {oy} {oz}">
      <freejoint name="box_freejoint"/>
      <inertial pos="0 0 0" mass="{object_mass}" diaginertia="0.0001 0.0001 0.0001"/>
      <geom name="box_geom" type="box" size="0.025 0.025 0.025" rgba="0.95 0.60 0.12 1.0" friction="{friction_coefficient} 0.01 0.0001"/>
    </body>

    <!-- 6-DOF Robotic Arm -->
    <body name="base_link" pos="0 0 0">
      <inertial pos="0.0 0.0 0.04" mass="4.0" fullinertia="0.021733 0.021733 0.0392 0.0 0.0 0.0"/>
      <geom name="base_link_geom" pos="0.0 0.0 0.04" rgba="0.2 0.3 0.4 1.0" type="cylinder" size="0.14 0.04"/>

      <!-- Link 1 (Yaw) -->
      <body name="link_1" pos="0.0 0.0 0.08">
        <joint name="joint_1" type="hinge" axis="0.0 0.0 1.0" range="-3.14159 3.14159" damping="0.5" frictionloss="0.1" armature="0.01"/>
        <inertial pos="0.0 0.0 0.06" mass="3.7" fullinertia="0.011933 0.011933 0.014985 0.0 0.0 0.0"/>
        <geom name="link_1_geom" pos="0.0 0.0 0.06" rgba="0.85 0.6 0.2 1.0" type="cylinder" size="0.09 0.06"/>

        <!-- Link 2 (Pitch) -->
        <body name="link_2" pos="0.0 0.0 0.12">
          <joint name="joint_2" type="hinge" axis="0.0 1.0 0.0" range="-1.5708 1.5708" damping="0.5" frictionloss="0.1" armature="0.01"/>
          <inertial pos="0.0 0.0 0.212" mass="8.39" fullinertia="0.130762 0.130762 0.008949 0.0 0.0 0.0"/>
          <geom name="link_2_geom" pos="0.0 0.0 0.212" rgba="0.85 0.6 0.2 1.0" type="box" size="0.04 0.04 0.2125"/>

          <!-- Link 3 (Pitch) -->
          <body name="link_3" pos="0.0 0.0 0.425">
            <joint name="joint_3" type="hinge" axis="0.0 1.0 0.0" range="-1.5708 1.5708" damping="0.4" frictionloss="0.08" armature="0.01"/>
            <inertial pos="0.0 0.0 0.196" mass="4.27" fullinertia="0.056422 0.056422 0.003487 0.0 0.0 0.0"/>
            <geom name="link_3_geom" pos="0.0 0.0 0.196" rgba="0.85 0.6 0.2 1.0" type="box" size="0.035 0.035 0.196"/>

            <!-- Link 4 (Pitch) -->
            <body name="link_4" pos="0.0 0.0 0.392">
              <joint name="joint_4" type="hinge" axis="0.0 1.0 0.0" range="-3.14159 3.14159" damping="0.2" frictionloss="0.04" armature="0.01"/>
              <inertial pos="0.0 0.0 0.045" mass="1.8" fullinertia="0.002126 0.002126 0.001822 0.0 0.0 0.0"/>
              <geom name="link_4_geom" pos="0.0 0.0 0.045" rgba="0.85 0.6 0.2 1.0" type="cylinder" size="0.045 0.045"/>

              <!-- Link 5 (Yaw) -->
              <body name="link_5" pos="0.0 0.0 0.09">
                <joint name="joint_5" type="hinge" axis="0.0 0.0 1.0" range="-3.14159 3.14159" damping="0.2" frictionloss="0.04" armature="0.01"/>
                <inertial pos="0.0 0.0 0.04" mass="1.5" fullinertia="0.0014 0.0014 0.0012 0.0 0.0 0.0"/>
                <geom name="link_5_geom" pos="0.0 0.0 0.04" rgba="0.85 0.6 0.2 1.0" type="cylinder" size="0.04 0.04"/>

                <!-- Link 6 (Flange) -->
                <body name="link_6" pos="0.0 0.0 0.08">
                  <joint name="joint_6" type="hinge" axis="1.0 0.0 0.0" range="-3.14159 3.14159" damping="0.1" frictionloss="0.02" armature="0.01"/>
                  <inertial pos="0.0 0.0 0.015" mass="0.87" fullinertia="0.000413 0.000413 0.000696 0.0 0.0 0.0"/>
                  <geom name="link_6_geom" pos="0.0 0.0 0.015" rgba="0.85 0.6 0.2 1.0" type="cylinder" size="0.04 0.015"/>

                  <!-- Parallel Jaw Gripper Assembly -->
                  <body name="gripper_base" pos="0.0 0.0 0.03">
                    <inertial pos="0.0 0.0 0.01" mass="0.30" diaginertia="0.0002 0.0002 0.0003"/>
                    <geom name="gripper_base_geom" pos="0.0 0.0 0.01" type="box" size="0.04 0.05 0.01" rgba="0.25 0.3 0.38 1.0" contype="0" conaffinity="0"/>

                    <!-- Left Gripper Finger -->
                    <body name="left_finger" pos="0.0 0.045 0.025">
                      <joint name="gripper_left" type="slide" axis="0.0 -1.0 0.0" range="0.0 0.038" damping="5.0"/>
                      <inertial pos="0.0 0.0 0.0" mass="0.06" diaginertia="0.00002 0.00002 0.00002"/>
                      <geom name="left_finger_geom" type="box" size="0.018 0.006 0.025" rgba="0.1 0.75 0.3 1.0" friction="{friction_coefficient} 0.01 0.0001"/>
                    </body>

                    <!-- Right Gripper Finger -->
                    <body name="right_finger" pos="0.0 -0.045 0.025">
                      <joint name="gripper_right" type="slide" axis="0.0 1.0 0.0" range="0.0 0.038" damping="5.0"/>
                      <inertial pos="0.0 0.0 0.0" mass="0.06" diaginertia="0.00002 0.00002 0.00002"/>
                      <geom name="right_finger_geom" type="box" size="0.018 0.006 0.025" rgba="0.1 0.75 0.3 1.0" friction="{friction_coefficient} 0.01 0.0001"/>
                    </body>
                  </body>
                </body>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>

  <contact>
    <!-- Exclude adjacent arm links from unphysical pivot self-collisions -->
    <exclude body1="base_link" body2="link_1"/>
    <exclude body1="link_1" body2="link_2"/>
    <exclude body1="link_2" body2="link_3"/>
    <exclude body1="link_3" body2="link_4"/>
    <exclude body1="link_4" body2="link_5"/>
    <exclude body1="link_5" body2="link_6"/>
    <exclude body1="link_6" body2="gripper_base"/>
    <exclude body1="gripper_base" body2="left_finger"/>
    <exclude body1="gripper_base" body2="right_finger"/>
    <exclude body1="left_finger" body2="right_finger"/>
  </contact>

  <actuator>
    <motor name="motor_joint_1" joint="joint_1" ctrlrange="-150.0 150.0"/>
    <motor name="motor_joint_2" joint="joint_2" ctrlrange="-150.0 150.0"/>
    <motor name="motor_joint_3" joint="joint_3" ctrlrange="-150.0 150.0"/>
    <motor name="motor_joint_4" joint="joint_4" ctrlrange="-28.0 28.0"/>
    <motor name="motor_joint_5" joint="joint_5" ctrlrange="-28.0 28.0"/>
    <motor name="motor_joint_6" joint="joint_6" ctrlrange="-28.0 28.0"/>
    <motor name="motor_gripper_left" joint="gripper_left" ctrlrange="0.0 30.0"/>
    <motor name="motor_gripper_right" joint="gripper_right" ctrlrange="0.0 30.0"/>
  </actuator>
</mujoco>
"""
    return mjcf_xml


def save_workcell_mjcf_file(target_path: str = "projects/default_6dof_arm/workcell.mjcf") -> Path:
    """Writes the workcell MJCF to the specified target path."""
    xml_str = generate_workcell_mjcf()
    out = Path(target_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml_str, encoding="utf-8")
    return out
