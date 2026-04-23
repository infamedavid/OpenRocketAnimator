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
        box1.label(text="1. Import OBJ")
        box1.prop(props, "obj_filepath", text="OBJ File")
        box1.operator("object.ora_import_obj", text="Import OBJ")
        box1.prop(props, "default_scale_factor")

        row_fix = box1.row(align=True)
        row_fix.operator("object.ora_fix_scale", text="Fix Scale")
        row_fix.operator("object.ora_clear_rotation", text="Clear Rotation")

        box2 = layout.box()
        box2.label(text="2. Load CSV Simulation")
        box2.prop(props, "csv_filepath", text="CSV File")

        box3 = layout.box()
        box3.label(text="3. Animation Options")
        box3.prop(props, "animate_rotation")
        #box3.prop(props, "animate_attitude")
        box3.prop(props, "frame_offset")
        box3.prop(props, "keyframe_step")
        box3.operator("object.ora_animate_csv", text="Animate from CSV")
        box3.operator("object.ora_convert_to_linear", text="Linear Animation")

        box4 = layout.box()
        box4.label(text="4. Camera Tools")
        box4.prop(props, "rocket_object")

        box_camera_track = box4.box()
        box_camera_track.label(text="Tracking Camera")
        box_camera_track.operator("view3d.object_as_camera", text="Set Selected Camera as Active")
        box_camera_track.operator("object.ora_track_rocket", text="Track Rocket")

        box_rocket_camera = box4.box()
        box_rocket_camera.label(text="Rocket Camera")
        box_rocket_camera.prop(props, "set_top_camera_active")
        box_rocket_camera.prop(props, "offset_z_camera")
        box_rocket_camera.prop(props, "offset_x_camera")
        box_rocket_camera.prop(props, "offset_y_camera")
        box_rocket_camera.prop(props, "rotation_z_camera")
        box_rocket_camera.prop(props, "adjust_clip_start")

        row = box_rocket_camera.row(align=True)
        row.operator("object.ora_add_rocket_camera", text="Add Rocket Camera")
        #row.operator("object.ora_update_rocket_camera", text="Update Camera")

        box_camera_noise = box4.box()
        box_camera_noise.label(text="Camera Shake (Noise)")
        box_camera_noise.prop(props, "noise_scale")
        box_camera_noise.prop(props, "noise_strength")
        box_camera_noise.prop(props, "noise_depth")
        box_camera_noise.operator("object.ora_add_camera_noise", text="Add Camera Noise")


classes = (
    ORA_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
