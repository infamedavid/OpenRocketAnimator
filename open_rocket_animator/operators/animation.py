import math
import os

import bpy

from ..core.animation_utils import iter_slot_fcurves
from ..core.csv_utils import (
    detect_header_and_data_start,
    find_header_index,
    iter_csv_rows,
    read_openrocket_csv_lines,
)


class ORA_OT_AnimateFromCSV(bpy.types.Operator):
    bl_idname = "object.ora_animate_csv"
    bl_label = "Animar desde CSV"

    def execute(self, context):
        props = context.scene.ora_props
        csv_path = bpy.path.abspath(props.csv_filepath)
        offset = props.frame_offset
        step = props.keyframe_step

        if not os.path.exists(csv_path):
            self.report({'ERROR'}, f"Archivo CSV no encontrado: {csv_path}")
            return {'CANCELLED'}

        obj = context.view_layer.objects.active
        if not obj or obj.type not in {'MESH', 'EMPTY'}:
            self.report({'ERROR'}, "Selecciona un objeto de tipo MESH o EMPTY para animar.")
            return {'CANCELLED'}

        try:
            lines = read_openrocket_csv_lines(csv_path)
            header, data_start = detect_header_and_data_start(lines)

            if not header:
                self.report({'ERROR'}, "No se encontró cabecera en el archivo CSV.")
                return {'CANCELLED'}

            if data_start is None:
                self.report({'ERROR'}, "No se encontraron datos en el archivo CSV.")
                return {'CANCELLED'}

            reader = iter_csv_rows(lines, data_start)

            time_idx = find_header_index(header, "Time")
            x_idx = find_header_index(header, "Position East")
            y_idx = find_header_index(header, "Position North")
            z_idx = find_header_index(header, "Altitude")
            roll_idx = find_header_index(header, "Roll rate") if props.animate_rotation else -1

            obj.animation_data_clear()
            scene = context.scene
            scene.frame_start = 0
            roll_angle = 0
            prev_time = 0
            max_frame = 0
            first_frame_written = False

            for row in reader:
                try:
                    t = float(row[time_idx])
                    x = float(row[x_idx])
                    y = float(row[y_idx])
                    z = float(row[z_idx])

                    if any(math.isnan(v) for v in [x, y, z]):
                        continue

                    frame = round(t * scene.render.fps) + offset

                    if not first_frame_written or frame % step == 0:
                        obj.location = (x, y, z)
                        obj.keyframe_insert(data_path="location", frame=frame)

                        if roll_idx != -1:
                            roll_rate = float(row[roll_idx])
                            if not math.isnan(roll_rate):
                                dt = t - prev_time
                                roll_angle += math.radians(roll_rate * dt)
                                obj.rotation_euler = (0, 0, roll_angle)
                                obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
                            prev_time = t

                        max_frame = max(max_frame, frame)
                        if not first_frame_written:
                            first_frame_written = True

                except Exception as exc:
                    print(f"Fila inválida omitida: {exc}")
                    continue

            scene.frame_end = max_frame
            self.report({'INFO'}, f"Animación generada hasta el frame {max_frame}.")
        except Exception as exc:
            self.report({'ERROR'}, f"Error leyendo CSV: {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}


class ORA_OT_ConvertToLinear(bpy.types.Operator):
    bl_idname = "object.ora_convert_to_linear"
    bl_label = "Animación Lineal"
    bl_description = "Convierte todas las curvas de animación del objeto activo a interpolación lineal (sin aceleración/desaceleración)"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'WARNING'}, "El objeto no tiene curvas de animación.")
            return {'CANCELLED'}

        has_curves = False
        for fcurve in iter_slot_fcurves(obj):
            has_curves = True
            for keyframe_point in fcurve.keyframe_points:
                keyframe_point.interpolation = 'LINEAR'

        if not has_curves:
            self.report({'WARNING'}, "El objeto no tiene curvas de animación.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Curvas de animación convertidas a lineales.")
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
