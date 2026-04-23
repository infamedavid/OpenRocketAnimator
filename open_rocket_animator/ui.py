import bpy


class ORA_PT_Panel(bpy.types.Panel):
    bl_label = "OpenRocket Animator"
    bl_idname = "ORA_PT_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OpenRocket"

    def draw(self, context):
        layout = self.layout
        props = context.scene.ora_props

        box1 = layout.box()
        box1.label(text="1. Importar Modelo OBJ")
        box1.prop(props, "obj_filepath")
        box1.operator("object.ora_import_obj")
        box1.prop(props, "default_scale_factor")
        box1.operator("object.ora_fix_scale")

        box2 = layout.box()
        box2.label(text="2. Cargar Simulación CSV")
        box2.prop(props, "csv_filepath")

        box3 = layout.box()
        box3.label(text="3. Opciones de Animación")
        box3.prop(props, "animate_rotation")
        box3.prop(props, "frame_offset")
        box3.prop(props, "keyframe_step")
        box3.operator("object.ora_animate_csv")
        box3.operator("object.ora_convert_to_linear")

        box4 = layout.box()
        box4.label(text="4. Manejo de Cámaras")

        box4.label(text="Cohete a seguir:")
        box4.prop(props, "rocket_name", text="")

        box_camera_track = box4.box()
        box_camera_track.label(text="Cámara de Seguimiento")
        box_camera_track.operator("view3d.object_as_camera", text="Set selected camera as active")
        box_camera_track.operator("object.ora_track_rocket", text="Track Rocket with active camera")

        box_rocket_camera = box4.box()
        box_rocket_camera.label(text="Cámara Cenital del Cohete")
        box_rocket_camera.prop(props, "set_top_camera_active")
        box_rocket_camera.prop(props, "offset_z_camera")
        box_rocket_camera.prop(props, "offset_x_camera")
        box_rocket_camera.prop(props, "adjust_clip_start")

        row = box_rocket_camera.row(align=True)
        row.operator("object.ora_add_rocket_camera", text="Add Rocket Camera")
        row.operator("object.ora_update_rocket_camera", text="Update Camera")

        box_camera_noise = box4.box()
        box_camera_noise.label(text="Efecto 'Shake' de Cámara (Noise)")
        box_camera_noise.prop(props, "noise_scale")
        box_camera_noise.prop(props, "noise_strength")
        box_camera_noise.prop(props, "noise_depth")
        box_camera_noise.operator("object.ora_add_camera_noise", text="Add Camera Noise / Shake")


classes = (
    ORA_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
