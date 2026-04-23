import bpy


class OpenRocketAnimProps(bpy.types.PropertyGroup):
    obj_filepath: bpy.props.StringProperty(
        name="OBJ File",
        subtype='FILE_PATH'
    )
    csv_filepath: bpy.props.StringProperty(
        name="CSV File",
        subtype='FILE_PATH'
    )
    animate_rotation: bpy.props.BoolProperty(
        name="Animate Rotation (Roll)",
        default=False
    )
    frame_offset: bpy.props.IntProperty(
        name="Start Offset (Frames)",
        default=0,
        min=0
    )
    default_scale_factor: bpy.props.FloatProperty(
        name="Scale Factor",
        description="Scale applied if the model is too large",
        default=0.001,
        min=0.0001,
        max=10.0
    )
    keyframe_step: bpy.props.IntProperty(
        name="Keyframe Frequency",
        description="Insert one keyframe every N frames",
        default=1,
        min=1,
        max=100
    )
    rocket_object: bpy.props.PointerProperty(
        name="Rocket Object",
        type=bpy.types.Object,
        description="Object used as the rocket target"
    )
    rocket_name: bpy.props.StringProperty(
        name="Rocket Name",
        description="Compatibility fallback: object name used as rocket target"
    )

    offset_z_camera: bpy.props.FloatProperty(
        name="Z Offset (m)",
        description="Vertical camera offset from the rocket top (for example, 0.05 for 5 cm up)",
        default=0.05,
        unit='LENGTH'
    )
    offset_x_camera: bpy.props.FloatProperty(
        name="X Offset (m)",
        description="Side camera offset from the rocket center (for example, -0.05 for 5 cm left)",
        default=-0.05,
        unit='LENGTH'
    )
    adjust_clip_start: bpy.props.BoolProperty(
        name="Adjust Clip Start",
        description="Set camera Clip Start to the absolute Z offset to avoid clipping",
        default=True
    )
    set_top_camera_active: bpy.props.BoolProperty(
        name="Set as Active Camera",
        description="Set the rocket top camera as active right after it is created",
        default=True
    )

    noise_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Noise texture scale (higher values produce larger motion)",
        default=0.25,
        min=0.01
    )
    noise_strength: bpy.props.FloatProperty(
        name="Strength",
        description="Noise intensity (higher values produce stronger shake)",
        default=0.005,
        min=0.0,
        max=0.015,
        step=0.001,
        precision=3
    )
    noise_depth: bpy.props.IntProperty(
        name="Depth",
        description="Number of noise octaves (higher values add detail)",
        default=5,
        min=0,
        max=10
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
