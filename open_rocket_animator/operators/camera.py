import bpy

from ..core.animation_utils import ensure_fcurve_for_datablock
from ..core.camera_utils import (
    apply_top_camera_transform,
    ensure_track_to_constraint,
    get_rocket_object,
)


class ORA_OT_TrackRocket(bpy.types.Operator):
    bl_idname = "object.ora_track_rocket"
    bl_label = "Track Rocket"

    def execute(self, context):
        props = context.scene.ora_props
        rocket_name = props.rocket_name

        if not rocket_name:
            self.report({'ERROR'}, "El campo 'Nombre del cohete' está vacío.")
            return {'CANCELLED'}

        rocket = get_rocket_object(rocket_name)
        if not rocket:
            self.report({'ERROR'}, f"No se encontró un objeto llamado '{rocket_name}'.")
            return {'CANCELLED'}

        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No hay cámara activa en la escena.")
            return {'CANCELLED'}

        constraint = cam.constraints.get("Track To")
        if not constraint:
            constraint = cam.constraints.new(type='TRACK_TO')
            constraint.name = "Track To"

        constraint.target = rocket
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        self.report({'INFO'}, f"La cámara activa ahora sigue al cohete '{rocket_name}'.")
        return {'FINISHED'}


class ORA_OT_AddRocketCamera(bpy.types.Operator):
    bl_idname = "object.ora_add_rocket_camera"
    bl_label = "Add Rocket Camera"
    bl_description = "Añade una cámara cenital emparentada al cohete, con opciones de offset y ajuste de clipping."

    def execute(self, context):
        props = context.scene.ora_props
        rocket_name = props.rocket_name

        if not rocket_name:
            self.report({'ERROR'}, "El campo 'Nombre del cohete' está vacío.")
            return {'CANCELLED'}

        rocket = get_rocket_object(rocket_name)
        if not rocket:
            self.report({'ERROR'}, f"No se encontró un objeto llamado '{rocket_name}'.")
            return {'CANCELLED'}

        cam_data = bpy.data.cameras.new(name="Rocket_Top_Camera")
        camera_obj = bpy.data.objects.new("Rocket_Top_Camera", cam_data)
        context.collection.objects.link(camera_obj)

        camera_obj.parent = rocket
        apply_top_camera_transform(camera_obj, rocket, props)
        ensure_track_to_constraint(camera_obj, rocket, constraint_name="Track To Rocket")

        if props.set_top_camera_active:
            context.scene.camera = camera_obj
            bpy.ops.object.select_all(action='DESELECT')
            camera_obj.select_set(True)
            context.view_layer.objects.active = camera_obj

        self.report({'INFO'}, f"Cámara cenital '{camera_obj.name}' creada y configurada para '{rocket_name}'.")
        return {'FINISHED'}


class ORA_OT_UpdateRocketCamera(bpy.types.Operator):
    bl_idname = "object.ora_update_rocket_camera"
    bl_label = "Update Camera"
    bl_description = "Actualiza la posición y el clipping de la cámara cenital existente según los offsets. Solo actualiza la primera cámara llamada 'Rocket_Top_Camera'."

    def execute(self, context):
        props = context.scene.ora_props
        rocket_name = props.rocket_name

        camera_obj = bpy.data.objects.get("Rocket_Top_Camera")
        if not camera_obj:
            self.report({'ERROR'}, "No se encontró la cámara 'Rocket_Top_Camera'. Por favor, créala primero.")
            return {'CANCELLED'}

        rocket = get_rocket_object(rocket_name)
        if not rocket:
            self.report({'ERROR'}, f"No se encontró un objeto llamado '{rocket_name}' para actualizar la cámara. El nombre del cohete puede haber cambiado o el objeto fue eliminado.")
            return {'CANCELLED'}

        if camera_obj.parent != rocket:
            camera_obj.parent = rocket
            self.report({'INFO'}, "La cámara 'Rocket_Top_Camera' ha sido re-emparentada al cohete especificado.")

        apply_top_camera_transform(camera_obj, rocket, props)
        ensure_track_to_constraint(camera_obj, rocket, constraint_name="Track To Rocket")

        self.report({'INFO'}, "Cámara cenital 'Rocket_Top_Camera' actualizada.")
        return {'FINISHED'}


class ORA_OT_AddCameraNoise(bpy.types.Operator):
    bl_idname = "object.ora_add_camera_noise"
    bl_label = "Add Camera Noise"
    bl_description = "Añade un modificador Noise a las curvas de Location X/Y de la cámara seleccionada para simular vibración/dramatismo."

    def execute(self, context):
        props = context.scene.ora_props

        camera_obj = None
        for obj in context.selected_objects:
            if obj.type == 'CAMERA':
                camera_obj = obj
                break

        if not camera_obj:
            self.report({'ERROR'}, "Por favor, selecciona una cámara en la escena para aplicar el ruido.")
            return {'CANCELLED'}

        if not camera_obj.animation_data:
            camera_obj.animation_data_create()

        current_frame = context.scene.frame_current
        camera_obj.keyframe_insert(data_path="location", frame=current_frame)

        if not camera_obj.animation_data or not camera_obj.animation_data.action:
            self.report({'WARNING'}, f"No se pudieron crear curvas de animación para la cámara '{camera_obj.name}'.")
            return {'CANCELLED'}

        data_paths_and_indices = [
            ("location", 0),
            ("location", 1),
        ]

        for data_path, index in data_paths_and_indices:
            # Blender 5 Action/Slot-compatible path.
            fcurve = ensure_fcurve_for_datablock(camera_obj, data_path, index=index)
            if not fcurve:
                self.report({'WARNING'}, f"No se pudo acceder a la curva '{data_path}' (índice {index}) de '{camera_obj.name}'.")
                return {'CANCELLED'}

            noise_modifier = None
            for modifier in fcurve.modifiers:
                if modifier.type == 'NOISE':
                    noise_modifier = modifier
                    break

            if not noise_modifier:
                noise_modifier = fcurve.modifiers.new(type='NOISE')

            noise_modifier.strength = props.noise_strength
            noise_modifier.scale = props.noise_scale
            noise_modifier.depth = props.noise_depth
            noise_modifier.blend_type = 'REPLACE'

            self.report({'INFO'}, f"Modificador Noise aplicado a la curva '{data_path}' de la cámara '{camera_obj.name}'.")

        return {'FINISHED'}


classes = (
    ORA_OT_TrackRocket,
    ORA_OT_AddRocketCamera,
    ORA_OT_UpdateRocketCamera,
    ORA_OT_AddCameraNoise,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
