from mathutils import Vector

import bpy

MOUNTED_CAMERA_NAME = "Rocket_Top_Camera"


def get_rocket_object(props):
    if getattr(props, "rocket_object", None):
        return props.rocket_object
    rocket_name = getattr(props, "rocket_name", "")
    if rocket_name:
        return bpy.data.objects.get(rocket_name)
    return None


def compute_local_bbox_mount(rocket):
    bbox_corners = [Vector(corner) for corner in rocket.bound_box]
    min_x = min(v.x for v in bbox_corners)
    max_x = max(v.x for v in bbox_corners)
    min_y = min(v.y for v in bbox_corners)
    max_y = max(v.y for v in bbox_corners)
    max_z = max(v.z for v in bbox_corners)
    return ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, max_z)


def find_mounted_rocket_camera(scene):
    cam_obj = scene.objects.get(MOUNTED_CAMERA_NAME)
    if cam_obj and cam_obj.type == 'CAMERA':
        return cam_obj
    obj = bpy.data.objects.get(MOUNTED_CAMERA_NAME)
    if obj and obj.type == 'CAMERA':
        return obj
    return None


def apply_live_camera_offsets(camera_obj, props):
    camera_obj.delta_location.x = props.offset_x_camera
    camera_obj.delta_location.y = 0.0
    camera_obj.delta_location.z = props.offset_z_camera

    if props.adjust_clip_start:
        clip_start = max(abs(props.offset_z_camera), 0.001)
        camera_obj.data.clip_start = clip_start
    else:
        camera_obj.data.clip_start = 0.1


def rebuild_rocket_camera_mount(camera_obj, rocket, props):
    base_x, base_y, top_z = compute_local_bbox_mount(rocket)
    camera_obj.parent = rocket
    camera_obj.location.x = base_x
    camera_obj.location.y = base_y
    camera_obj.location.z = top_z
    camera_obj.rotation_euler = (0.0, 0.0, 0.0)
    apply_live_camera_offsets(camera_obj, props)
