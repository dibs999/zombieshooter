"""Original facility art kit; meters, Z-up, exported to Godot glTF Y-up.

Run: blender --background --python-exit-code 1 --python tools/blender/gen_facility_details.py
Only these three assets are rebuilt. No external images or downloaded models.
"""
import math
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as C


def materials():
    return (
        C.make_pbr_mat("FacilityPaint", (0.23, 0.28, 0.27, 1), metallic=0.55, roughness=0.64),
        C.make_pbr_mat("ExposedSteel", (0.34, 0.32, 0.27, 1), metallic=0.8, roughness=0.42),
        C.make_pbr_mat("SafetyOchre", (0.72, 0.46, 0.08, 1), metallic=0.25, roughness=0.7),
        C.make_pbr_mat("Rubber", (0.045, 0.05, 0.055, 1), roughness=0.92),
        C.make_pbr_mat("Phosphor", (0.08, 0.5, 0.39, 1), roughness=0.3,
                       emission=(0.12, 0.85, 0.65), emission_strength=1.2),
    )


def build_console():
    C.reset_scene()
    paint, steel, ochre, rubber, screen = materials()
    parts = [
        C.add_box("Foot", (0.68, 0.58, 0.12), (0, 0, 0.06), mat=steel, bevel=0.025),
        C.add_box("Pedestal", (0.48, 0.38, 0.9), (0, 0, 0.55), mat=paint, bevel=0.025),
        C.add_box("ControlHead", (0.72, 0.50, 0.42), (0, 0, 1.18), mat=paint, bevel=0.04),
        C.add_box("ScreenBezel", (0.52, 0.06, 0.25), (0, -0.27, 1.23), mat=rubber, bevel=0.018),
        C.add_box("CRTGlass", (0.43, 0.014, 0.17), (0, -0.306, 1.23), mat=screen, bevel=0.012),
    ]
    for x in (-0.25, 0.25):
        for z in (0.25, 0.75):
            parts.append(C.add_cyl("PanelBolt", 0.025, 0.025, (x, -0.205, z),
                                   (math.pi / 2, 0, 0), vertices=8, mat=steel))
    for i in range(5):
        parts.append(C.add_box("Vent", (0.28, 0.02, 0.018), (0, -0.201, 0.4 + i * 0.045), mat=rubber))
    for x in (-0.24, 0.0, 0.24):
        parts.append(C.add_cyl("Button", 0.04, 0.04, (x, -0.27, 1.06),
                               (math.pi / 2, 0, 0), mat=ochre))
    C.join_objects(parts, "EmergencyTransferConsole")
    C.export_asset("env", "teleporter_console")


def build_arch():
    C.reset_scene()
    paint, steel, ochre, rubber, _ = materials()
    # Clear opening matches existing 3.4 m doorways; geometry stays outside it.
    parts = []
    for x in (-1.88, 1.88):
        parts.append(C.add_box("Jamb", (0.30, 0.65, 3.35), (x, 0, 1.675), mat=paint, bevel=0.025))
        parts.append(C.add_box("FootGuard", (0.34, 0.70, 0.55), (x, 0, 0.275), mat=ochre, bevel=0.015))
        for z in (0.75, 1.5, 2.25, 3.0):
            parts.append(C.add_cyl("Rivet", 0.035, 0.025, (x, -0.34, z),
                                   (math.pi / 2, 0, 0), vertices=8, mat=steel))
    parts.append(C.add_box("Lintel", (4.1, 0.7, 0.36), (0, 0, 3.42), mat=paint, bevel=0.025))
    for x in range(-7, 8):
        parts.append(C.add_box("WarningStripe", (0.11, 0.02, 0.26),
                               (x * 0.25, -0.365, 3.42), (0, -0.38, 0), mat=ochre))
    C.join_objects(parts, "ContainmentBulkhead")
    C.export_asset("env", "containment_arch")


def build_pipes():
    C.reset_scene()
    paint, steel, ochre, rubber, _ = materials()
    parts = []
    for z, radius in ((0.0, 0.085), (0.28, 0.06), (0.51, 0.045)):
        parts.append(C.add_cyl("ServiceLine", radius, 4.0, (0, 0, z), (0, math.pi / 2, 0), mat=steel))
        for x in (-1.7, 0, 1.7):
            parts.append(C.add_cyl("Flange", radius * 1.35, 0.07, (x, 0, z),
                                   (0, math.pi / 2, 0), vertices=12, mat=paint))
    for x in (-1.5, 1.5):
        parts.append(C.add_box("WallBracket", (0.09, 0.2, 0.76), (x, 0.06, 0.25), mat=paint))
    parts.append(C.add_torus("ShutoffWheel", 0.19, 0.022, (0.7, -0.18, 0), (math.pi / 2, 0, 0), mat=ochre))
    for angle in (0, math.pi / 3, math.pi * 2 / 3):
        parts.append(C.add_cyl("WheelSpoke", 0.012, 0.36, (0.7, -0.18, 0), (0, angle, 0), mat=ochre))
    C.join_objects(parts, "ServicePipeManifold")
    C.export_asset("env", "service_pipes")


build_console()
build_arch()
build_pipes()
