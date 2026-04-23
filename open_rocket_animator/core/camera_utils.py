import bpy
from mathutils import Vector


def get_rocket_object(rocket_name):
    if not rocket_name:
        return None
    return bpy.data.objects.get(rocket_name)


def compute_local_bbox_centers(rocket):
    bbox_corners_local = [Vector(corner) for corner in rocket.bound_box]
    bbox_max_z_local = max(v.z for v in bbox_corners_local)
    bbox_min_x_local = min(v.x for v in bbox_corners_local)
    bbox_max_x_local = max(v.x for v in bbox_corners_local)
    bbox_center_x_local = (bbox_min_x_local + bbox_max_x_local) / 2
    bbox_min_y_local = min(v.y for v in bbox_corners_local)
    bbox_max_y_local = max(v.y for v in bbox_corners_local)
    bbox_center_y_local = (bbox_min_y_local + bbox_max_y_local) / 2
    return bbox_center_x_local, bbox_center_y_local, bbox_max_z_local


def apply_top_camera_transform(camera_obj, rocket, props):
    bbox_center_x_local, bbox_center_y_local, bbox_max_z_local = compute_local_bbox_centers(rocket)

    camera_obj.location.x = bbox_center_x_local + props.offset_x_camera
    camera_obj.location.y = bbox_center_y_local
    camera_obj.location.z = bbox_max_z_local + props.offset_z_camera

    camera_obj.rotation_euler = (0, 0, 0)

    if props.adjust_clip_start:
        new_clip_start = abs(props.offset_z_camera)
        if new_clip_start < 0.001:
            new_clip_start = 0.001
        camera_obj.data.clip_start = new_clip_start
    else:
        camera_obj.data.clip_start = 0.1


def ensure_track_to_constraint(camera_obj, rocket, constraint_name="Track To Rocket"):
    constraint = camera_obj.constraints.get(constraint_name)
    if not constraint:
        constraint = camera_obj.constraints.new(type='TRACK_TO')
        constraint.name = constraint_name

    constraint.target = rocket
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    return constraint
