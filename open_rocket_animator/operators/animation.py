import os

import bpy

from ..core.animation_utils import compute_attitude_euler, iter_slot_fcurves
from ..core.csv_utils import (
    detect_header_and_data_start,
    find_header_index,
    find_orientation_indices,
    iter_csv_rows,
    read_openrocket_csv_lines,
    safe_float,
)


class ORA_OT_AnimateFromCSV(bpy.types.Operator):
    bl_idname = "object.ora_animate_csv"
    bl_label = "Animate from CSV"

    def execute(self, context):
        props = context.scene.ora_props
        csv_path = bpy.path.abspath(props.csv_filepath)

        if not os.path.exists(csv_path):
            self.report({'ERROR'}, f"CSV file not found: {csv_path}")
            return {'CANCELLED'}

        obj = context.view_layer.objects.active
        if not obj or obj.type not in {'MESH', 'EMPTY'}:
            self.report({'ERROR'}, "Select a MESH or EMPTY object to animate.")
            return {'CANCELLED'}

        try:
            lines = read_openrocket_csv_lines(csv_path)
            header, data_start = detect_header_and_data_start(lines)
            if not header:
                self.report({'ERROR'}, "CSV header was not found.")
                return {'CANCELLED'}
            if data_start is None:
                self.report({'ERROR'}, "No data rows were found in the CSV file.")
                return {'CANCELLED'}

            time_idx = find_header_index(header, "Time")
            x_idx = find_header_index(header, "Position East")
            y_idx = find_header_index(header, "Position North")
            z_idx = find_header_index(header, "Altitude")

            if min(time_idx, x_idx, y_idx, z_idx) < 0:
                self.report({'ERROR'}, "Required position columns were not found in the CSV file.")
                return {'CANCELLED'}

            ori_indices = find_orientation_indices(header)
            roll_idx = ori_indices["roll_rate"] if props.animate_rotation else -1
            vertical_idx = ori_indices["vertical"] if props.animate_attitude else -1
            lateral_idx = ori_indices["lateral"] if props.animate_attitude else -1

            if props.animate_attitude and (vertical_idx < 0 or lateral_idx < 0):
                self.report({'WARNING'}, "Attitude columns not found. Continuing without attitude animation.")
                vertical_idx = -1
                lateral_idx = -1

            obj.animation_data_clear()

            scene = context.scene
            scene.frame_start = 0
            frame_offset = props.frame_offset
            step = props.keyframe_step
            max_frame = 0

            prev_time_for_roll = None
            roll_angle = 0.0
            first_frame_written = False

            for row in iter_csv_rows(lines, data_start):
                if not row:
                    continue
                if row[0].strip().startswith('#'):
                    continue

                try:
                    t = safe_float(row[time_idx])
                    x = safe_float(row[x_idx])
                    y = safe_float(row[y_idx])
                    z = safe_float(row[z_idx])
                except Exception:
                    continue

                if None in (t, x, y, z):
                    continue

                frame = round(t * scene.render.fps) + frame_offset
                if first_frame_written and frame % step != 0:
                    continue

                obj.location = (x, y, z)
                obj.keyframe_insert(data_path="location", frame=frame)

                roll_for_frame = None
                if roll_idx >= 0 and roll_idx < len(row):
                    roll_rate = safe_float(row[roll_idx])
                    if roll_rate is not None:
                        if prev_time_for_roll is None:
                            prev_time_for_roll = t
                        dt = t - prev_time_for_roll
                        roll_angle += (roll_rate * dt) * 0.017453292519943295
                        prev_time_for_roll = t
                        roll_for_frame = roll_angle

                attitude_euler = None
                if vertical_idx >= 0 and lateral_idx >= 0 and vertical_idx < len(row) and lateral_idx < len(row):
                    vertical = safe_float(row[vertical_idx])
                    lateral = safe_float(row[lateral_idx])
                    if vertical is not None and lateral is not None:
                        attitude_euler = compute_attitude_euler(vertical, lateral, 0.0)

                if attitude_euler is not None or roll_for_frame is not None:
                    current_euler = list(obj.rotation_euler)
                    if attitude_euler is not None:
                        current_euler = [attitude_euler[0], attitude_euler[1], attitude_euler[2]]
                    if roll_for_frame is not None:
                        # Keep legacy roll axis behavior: roll is applied to Euler Z.
                        current_euler[2] = current_euler[2] + roll_for_frame if attitude_euler is not None else roll_for_frame
                    obj.rotation_euler = tuple(current_euler)
                    obj.keyframe_insert(data_path="rotation_euler", frame=frame)

                max_frame = max(max_frame, frame)
                first_frame_written = True

            scene.frame_end = max_frame
            self.report({'INFO'}, f"Animation generated up to frame {max_frame}.")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Error reading CSV: {exc}")
            return {'CANCELLED'}


class ORA_OT_ConvertToLinear(bpy.types.Operator):
    bl_idname = "object.ora_convert_to_linear"
    bl_label = "Linear Animation"
    bl_description = "Convert all animation curves on the active object to linear interpolation"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'WARNING'}, "No active object.")
            return {'CANCELLED'}

        curves = list(iter_slot_fcurves(obj) or [])
        if not curves:
            self.report({'WARNING'}, "No slot-aware animation curves were found on the active object.")
            return {'CANCELLED'}

        for fcurve in curves:
            for keyframe_point in fcurve.keyframe_points:
                keyframe_point.interpolation = 'LINEAR'

        self.report({'INFO'}, "Animation curves converted to linear.")
        return {'FINISHED'}


classes = (
    ORA_OT_AnimateFromCSV,
    ORA_OT_ConvertToLinear,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
