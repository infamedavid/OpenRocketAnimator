import bpy

from ..core.animation_utils import find_or_create_slot_fcurve
from ..core.camera_utils import (
    MOUNTED_CAMERA_NAME,
    apply_live_camera_offsets,
    find_mounted_rocket_camera,
    get_rocket_object,
    rebuild_rocket_camera_mount,
)


class ORA_OT_TrackRocket(bpy.types.Operator):
    bl_idname = "object.ora_track_rocket"
    bl_label = "Track Rocket"

    def execute(self, context):
        props = context.scene.ora_props
        rocket = get_rocket_object(props)
        if not rocket:
            self.report({'ERROR'}, "No valid rocket object selected.")
            return {'CANCELLED'}

        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No active scene camera.")
            return {'CANCELLED'}

        constraint = cam.constraints.get("Track To")
        if not constraint:
            constraint = cam.constraints.new(type='TRACK_TO')
            constraint.name = "Track To"

        constraint.target = rocket
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        self.report({'INFO'}, f"Active camera now tracks '{rocket.name}'.")
        return {'FINISHED'}


class ORA_OT_AddRocketCamera(bpy.types.Operator):
    bl_idname = "object.ora_add_rocket_camera"
    bl_label = "Add Rocket Camera"

    def execute(self, context):
        props = context.scene.ora_props
        rocket = get_rocket_object(props)
        if not rocket:
            self.report({'ERROR'}, "No valid rocket object selected.")
            return {'CANCELLED'}

        cam_data = bpy.data.cameras.new(name=MOUNTED_CAMERA_NAME)
        camera_obj = bpy.data.objects.new(MOUNTED_CAMERA_NAME, cam_data)
        context.collection.objects.link(camera_obj)

        rebuild_rocket_camera_mount(camera_obj, rocket, props)

        for constraint in list(camera_obj.constraints):
            if constraint.type == 'TRACK_TO':
                camera_obj.constraints.remove(constraint)

        if props.set_top_camera_active:
            context.scene.camera = camera_obj
            bpy.ops.object.select_all(action='DESELECT')
            camera_obj.select_set(True)
            context.view_layer.objects.active = camera_obj

        self.report({'INFO'}, f"Rocket camera '{camera_obj.name}' created.")
        return {'FINISHED'}


class ORA_OT_UpdateRocketCamera(bpy.types.Operator):
    bl_idname = "object.ora_update_rocket_camera"
    bl_label = "Update Camera"

    def execute(self, context):
        props = context.scene.ora_props
        camera_obj = find_mounted_rocket_camera(context.scene)
        if not camera_obj:
            self.report({'ERROR'}, f"Camera '{MOUNTED_CAMERA_NAME}' was not found. Create it first.")
            return {'CANCELLED'}

        rocket = get_rocket_object(props)
        if not rocket:
            self.report({'ERROR'}, "No valid rocket object selected.")
            return {'CANCELLED'}

        rebuild_rocket_camera_mount(camera_obj, rocket, props)

        for constraint in list(camera_obj.constraints):
            if constraint.type == 'TRACK_TO':
                camera_obj.constraints.remove(constraint)

        self.report({'INFO'}, "Rocket camera base mount rebuilt.")
        return {'FINISHED'}


class ORA_OT_AddCameraNoise(bpy.types.Operator):
    bl_idname = "object.ora_add_camera_noise"
    bl_label = "Add Camera Noise"

    def execute(self, context):
        props = context.scene.ora_props

        camera_obj = None
        for obj in context.selected_objects:
            if obj.type == 'CAMERA':
                camera_obj = obj
                break

        if not camera_obj:
            self.report({'ERROR'}, "Select a camera to apply noise.")
            return {'CANCELLED'}

        if not camera_obj.animation_data:
            camera_obj.animation_data_create()

        current_frame = context.scene.frame_current
        camera_obj.keyframe_insert(data_path="location", frame=current_frame)

        targets = (("location", 0), ("location", 1))
        for data_path, index in targets:
            fcurve = find_or_create_slot_fcurve(camera_obj, data_path, index)
            if not fcurve:
                self.report({'WARNING'}, f"Could not access curve {data_path}[{index}] on '{camera_obj.name}'.")
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

        self.report({'INFO'}, f"Camera noise applied to '{camera_obj.name}'.")
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
