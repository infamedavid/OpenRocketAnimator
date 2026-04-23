import bpy

from .core.camera_utils import apply_live_camera_offsets, find_mounted_rocket_camera


def _update_mounted_camera_from_props(self, context):
    scene = context.scene if context else None
    if scene is None:
        return
    camera_obj = find_mounted_rocket_camera(scene)
    if camera_obj is None:
        return
    apply_live_camera_offsets(camera_obj, self)


class OpenRocketAnimProps(bpy.types.PropertyGroup):
    obj_filepath: bpy.props.StringProperty(
        name="OBJ File",
        description="Path to the OBJ file to import",
        subtype='FILE_PATH',
    )
    csv_filepath: bpy.props.StringProperty(
        name="CSV File",
        description="Path to the OpenRocket CSV simulation file",
        subtype='FILE_PATH',
    )
    animate_rotation: bpy.props.BoolProperty(
        name="Animate Roll",
        description="Animate rocket roll from CSV roll rate",
        default=False,
    )
    animate_attitude: bpy.props.BoolProperty(
        name="Animate Attitude",
        description="Animate rocket attitude from CSV orientation columns",
        default=False,
    )
    frame_offset: bpy.props.IntProperty(
        name="Start Offset (Frames)",
        default=0,
        min=0,
    )
    default_scale_factor: bpy.props.FloatProperty(
        name="Scale Factor",
        description="Scale applied if the imported model is too large",
        default=0.001,
        min=0.0001,
        max=10.0,
    )
    keyframe_step: bpy.props.IntProperty(
        name="Keyframe Frequency",
        description="Insert one keyframe every N sampled frames",
        default=1,
        min=1,
        max=100,
    )

    rocket_object: bpy.props.PointerProperty(
        name="Rocket Object",
        type=bpy.types.Object,
        description="Object used as the rocket target",
    )
    rocket_name: bpy.props.StringProperty(
        name="Rocket Name",
        description="Backward-compatibility fallback rocket object name",
    )

    offset_z_camera: bpy.props.FloatProperty(
        name="Z Offset (m)",
        description="Vertical mounted camera offset from rocket top",
        default=0.05,
        unit='LENGTH',
        update=_update_mounted_camera_from_props,
    )
    offset_x_camera: bpy.props.FloatProperty(
        name="X Offset (m)",
        description="Lateral mounted camera offset from rocket center",
        default=-0.05,
        unit='LENGTH',
        update=_update_mounted_camera_from_props,
    )
    adjust_clip_start: bpy.props.BoolProperty(
        name="Adjust Clip Start",
        description="Set camera clip start from mounted camera offset",
        default=True,
        update=_update_mounted_camera_from_props,
    )
    set_top_camera_active: bpy.props.BoolProperty(
        name="Set as Active Camera",
        description="Set the mounted rocket camera as the active scene camera when created",
        default=True,
    )

    noise_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Noise scale",
        default=0.25,
        min=0.01,
    )
    noise_strength: bpy.props.FloatProperty(
        name="Strength",
        description="Noise strength",
        default=0.005,
        min=0.0,
        max=0.015,
        step=0.001,
        precision=3,
    )
    noise_depth: bpy.props.IntProperty(
        name="Depth",
        description="Noise detail depth",
        default=5,
        min=0,
        max=10,
    )


classes = (
    OpenRocketAnimProps,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ora_props = bpy.props.PointerProperty(type=OpenRocketAnimProps)


def unregister():
    if hasattr(bpy.types.Scene, "ora_props"):
        del bpy.types.Scene.ora_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
