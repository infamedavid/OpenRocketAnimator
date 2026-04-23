bl_info = {
    "name": "OpenRocket Animator",
    "author": "infamedavid",
    "version": (2, 3),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Sidebar > OpenRocket",
    "description": "Import an OBJ model and animate it using OpenRocket CSV data.",
    "category": "Import-Export",
}

import importlib

from . import properties
from .operators import import_obj, animation, camera
from . import ui

MODULES = (
    properties,
    import_obj,
    animation,
    camera,
    ui,
)

# Optional root-only reload support for development.
if "bpy" in locals():
    for _module in MODULES:
        importlib.reload(_module)


classes = ()


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
