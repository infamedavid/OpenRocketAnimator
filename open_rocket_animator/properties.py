import bpy


class OpenRocketAnimProps(bpy.types.PropertyGroup):
    obj_filepath: bpy.props.StringProperty(
        name="Archivo OBJ",
        subtype='FILE_PATH'
    )
    csv_filepath: bpy.props.StringProperty(
        name="Archivo CSV",
        subtype='FILE_PATH'
    )
    animate_rotation: bpy.props.BoolProperty(
        name="Animar Rotación (Roll)",
        default=False
    )
    frame_offset: bpy.props.IntProperty(
        name="Offset de inicio (frames)",
        default=0,
        min=0
    )
    default_scale_factor: bpy.props.FloatProperty(
        name="Factor de escala",
        description="Escala aplicada si el modelo es muy grande",
        default=0.001,
        min=0.0001,
        max=10.0
    )
    keyframe_step: bpy.props.IntProperty(
        name="Frecuencia de keyframes",
        description="Insertar un keyframe cada N frames",
        default=1,
        min=1,
        max=100
    )
    rocket_name: bpy.props.StringProperty(
        name="Nombre del cohete",
        description="Nombre del objeto a seguir con la cámara"
    )

    offset_z_camera: bpy.props.FloatProperty(
        name="Offset Z (m)",
        description="Desplazamiento vertical de la cámara respecto al tope del cohete (ej. 0.05 para 5cm arriba)",
        default=0.05,
        unit='LENGTH'
    )
    offset_x_camera: bpy.props.FloatProperty(
        name="Offset X (m)",
        description="Desplazamiento lateral de la cámara respecto al centro del cohete (ej. -0.05 para 5cm a la izquierda)",
        default=-0.05,
        unit='LENGTH'
    )
    adjust_clip_start: bpy.props.BoolProperty(
        name="Ajustar Clip Start",
        description="Ajusta el 'Clip Start' de la cámara al valor absoluto del Offset Z para evitar clipping",
        default=True
    )
    set_top_camera_active: bpy.props.BoolProperty(
        name="Set as Active Camera",
        description="Activa la cámara cenital automáticamente al añadirla",
        default=True
    )

    noise_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Escala de la textura de ruido (mayor valor = ruido más grande)",
        default=0.25,
        min=0.01
    )
    noise_strength: bpy.props.FloatProperty(
        name="Strength",
        description="Intensidad del ruido (mayor valor = mayor sacudida)",
        default=0.005,
        min=0.0,
        max=0.015,
        step=0.001,
        precision=3
    )
    noise_depth: bpy.props.IntProperty(
        name="Depth",
        description="Número de octavas de ruido (mayor valor = ruido más detallado)",
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
