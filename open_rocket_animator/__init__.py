bl_info = {
    "name": "OpenRocket OBJ + CSV Animator",
    "author": "infamedavid",
    "version": (2, 2),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Sidebar > OpenRocket Panel",
    "description": "Import an OBJ model and animate its movement using OpenRocket simulation CSV data.",
    "category": "Import-Export",
}

import importlib

from . import properties
from .operators import animation, camera, import_obj
from . import ui

MODULES = [
    properties,
    import_obj,
    animation,
    camera,
    ui,
]


if "bpy" in locals():
    for module in MODULES:
        importlib.reload(module)


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
