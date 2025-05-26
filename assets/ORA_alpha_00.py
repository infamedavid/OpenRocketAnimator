bl_info = {
    "name": "OpenRocket OBJ + CSV Animator",
    "author": "effetagroove@gmail.com",
    "version": (alpha 0),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Sidebar > OpenRocket Panel",
    "description": "Importa un modelo OBJ y anima su movimiento usando datos de simulación de OpenRocket.",
    "category": "Import-Export",
}

import bpy
import csv
import os
import math

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

class ORA_OT_ImportOBJ(bpy.types.Operator):
    bl_idname = "object.ora_import_obj"
    bl_label = "Importar OBJ"

    def execute(self, context):
        path = bpy.path.abspath(context.scene.ora_props.obj_filepath)
        if not os.path.exists(path):
            self.report({'ERROR'}, f"No se encuentra el archivo: {path}")
            return {'CANCELLED'}

        try:
            bpy.ops.wm.obj_import(filepath=path)

            obj = context.view_layer.objects.active
            if obj:
                self.report({'INFO'}, "Modelo OBJ importado correctamente. Puedes corregir la escala si es necesario.")
        except Exception as e:
            self.report({'ERROR'}, f"Error al importar OBJ: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class ORA_OT_FixScale(bpy.types.Operator):
    bl_idname = "object.ora_fix_scale"
    bl_label = "Corregir Escala"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'ERROR'}, "No hay objeto activo para escalar.")
            return {'CANCELLED'}

        factor = context.scene.ora_props.default_scale_factor
        obj.scale = (factor, factor, factor)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        self.report({'INFO'}, f"Escala corregida y aplicada con factor {factor}.")
        return {'FINISHED'}

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
            with open(csv_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()

            header = None
            for i, line in enumerate(lines):
                if line.strip().startswith('#') and ',' in line:
                    header = line.strip().lstrip('#').strip().split(',')
                elif not line.strip().startswith('#'):
                    data_start = i
                    break

            if not header:
                self.report({'ERROR'}, "No se encontró cabecera en el archivo CSV.")
                return {'CANCELLED'}

            reader = csv.reader(lines[data_start:])

            def find_index(name):
                for i, h in enumerate(header):
                    if name in h:
                        return i
                raise ValueError(f"'{name}' no encontrado en el encabezado")

            time_idx = find_index("Time")
            x_idx = find_index("Position East")
            y_idx = find_index("Position North")
            z_idx = find_index("Altitude")
            roll_idx = find_index("Roll rate") if props.animate_rotation else -1

            obj.animation_data_clear()
            scene = context.scene
            scene.frame_start = 0
            roll_angle = 0
            prev_time = 0
            max_frame = 0

            for row in reader:
                try:
                    t = float(row[time_idx])
                    x = float(row[x_idx])
                    y = float(row[y_idx])
                    z = float(row[z_idx])

                    if any(math.isnan(v) for v in [x, y, z]):
                        continue

                    frame = round(t * scene.render.fps) + offset
                    if frame % step != 0:
                        continue

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

                except Exception as e:
                    print(f"Fila inválida omitida: {e}")
                    continue

            scene.frame_end = max_frame
            self.report({'INFO'}, f"Animación generada hasta el frame {max_frame}.")
        except Exception as e:
            self.report({'ERROR'}, f"Error leyendo CSV: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class ORA_PT_Panel(bpy.types.Panel):
    bl_label = "OpenRocket Animator"
    bl_idname = "ORA_PT_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OpenRocket"

    def draw(self, context):
        layout = self.layout
        props = context.scene.ora_props

        layout.label(text="1. Importar Modelo OBJ")
        layout.prop(props, "obj_filepath")
        layout.operator("object.ora_import_obj")
        layout.prop(props, "default_scale_factor")
        layout.operator("object.ora_fix_scale")

        layout.separator()
        layout.label(text="2. Cargar Simulación CSV")
        layout.prop(props, "csv_filepath")
        layout.prop(props, "animate_rotation")
        layout.operator("object.ora_animate_csv")

        layout.separator()
        layout.label(text="3. Opciones de Animación")
        layout.prop(props, "frame_offset")
        layout.prop(props, "keyframe_step")

def register():
    bpy.utils.register_class(OpenRocketAnimProps)
    bpy.utils.register_class(ORA_OT_ImportOBJ)
    bpy.utils.register_class(ORA_OT_FixScale)
    bpy.utils.register_class(ORA_OT_AnimateFromCSV)
    bpy.utils.register_class(ORA_PT_Panel)
    bpy.types.Scene.ora_props = bpy.props.PointerProperty(type=OpenRocketAnimProps)

def unregister():
    bpy.utils.unregister_class(OpenRocketAnimProps)
    bpy.utils.unregister_class(ORA_OT_ImportOBJ)
    bpy.utils.unregister_class(ORA_OT_FixScale)
    bpy.utils.unregister_class(ORA_OT_AnimateFromCSV)
    bpy.utils.unregister_class(ORA_PT_Panel)
    del bpy.types.Scene.ora_props

if __name__ == "__main__":
    register()
