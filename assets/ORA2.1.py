import bpy
import csv
import os
import math
from mathutils import Vector 

bl_info = {
    "name": "OpenRocket OBJ + CSV Animator",
    "author": "effetagroove@gmail.com",
    "version": (2, 1), # He incrementado la versión a 2.1 por las nuevas características y correcciones
    "blender": (4, 0, 0),
    "location": "3D Viewport > Sidebar > OpenRocket Panel",
    "description": "Importa un modelo OBJ y anima su movimiento usando datos de simulación de OpenRocket.",
    "category": "Import-Export",
}


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
    
    # --- Nuevas propiedades para el modificador Noise ---
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
        step=0.001, # Para un control más fino en la UI
        precision=3 # Para mostrar 3 decimales
    )
    noise_depth: bpy.props.IntProperty(
        name="Depth",
        description="Número de octavas de ruido (mayor valor = ruido más detallado)",
        default=5,
        min=0,
        max=10
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

                except Exception as e:
                    print(f"Fila inválida omitida: {e}")
                    continue

            scene.frame_end = max_frame
            self.report({'INFO'}, f"Animación generada hasta el frame {max_frame}.")
        except Exception as e:
            self.report({'ERROR'}, f"Error leyendo CSV: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class ORA_OT_ConvertToLinear(bpy.types.Operator):
    bl_idname = "object.ora_convert_to_linear"
    bl_label = "Animación Lineal"
    bl_description = "Convierte todas las curvas de animación del objeto activo a interpolación lineal (sin aceleración/desaceleración)"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "El objeto no tiene curvas de animación.")
            return {'CANCELLED'}

        for fcurve in obj.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

        self.report({'INFO'}, "Curvas de animación convertidas a lineales.")
        return {'FINISHED'}

class ORA_OT_TrackRocket(bpy.types.Operator):
    bl_idname = "object.ora_track_rocket"
    bl_label = "Track Rocket"

    def execute(self, context):
        props = context.scene.ora_props
        rocket_name = props.rocket_name

        if not rocket_name:
            self.report({'ERROR'}, "El campo 'Nombre del cohete' está vacío.")
            return {'CANCELLED'}

        rocket = bpy.data.objects.get(rocket_name)
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

# --- OPERADOR PARA AÑADIR LA CÁMARA CENITAL ---
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

        rocket = bpy.data.objects.get(rocket_name)
        if not rocket:
            self.report({'ERROR'}, f"No se encontró un objeto llamado '{rocket_name}'.")
            return {'CANCELLED'}

        # 1. Crear una nueva cámara
        cam_data = bpy.data.cameras.new(name="Rocket_Top_Camera") 
        camera_obj = bpy.data.objects.new("Rocket_Top_Camera", cam_data)
        context.collection.objects.link(camera_obj)

        # 2. Emparentar la cámara al cohete
        camera_obj.parent = rocket
        
        # 3. Calcular la posición local de la cámara (relativa al cohete)
        bbox_corners_local = [Vector(corner) for corner in rocket.bound_box]
        bbox_max_z_local = max(v.z for v in bbox_corners_local)
        bbox_min_x_local = min(v.x for v in bbox_corners_local)
        bbox_max_x_local = max(v.x for v in bbox_corners_local)
        bbox_center_x_local = (bbox_min_x_local + bbox_max_x_local) / 2
        bbox_min_y_local = min(v.y for v in bbox_corners_local)
        bbox_max_y_local = max(v.y for v in bbox_corners_local)
        bbox_center_y_local = (bbox_min_y_local + bbox_max_y_local) / 2
        
        camera_obj.location.x = bbox_center_x_local + props.offset_x_camera
        camera_obj.location.y = bbox_center_y_local 
        camera_obj.location.z = bbox_max_z_local + props.offset_z_camera

        # 4. Establecer la rotación de la cámara (identidad, para que el Track To funcione como se espera)
        camera_obj.rotation_euler = (0, 0, 0) 
        
        # 5. Ajustar el clipping de la cámara
        if props.adjust_clip_start:
            new_clip_start = abs(props.offset_z_camera) 
            if new_clip_start < 0.001:
                new_clip_start = 0.001
            camera_obj.data.clip_start = new_clip_start
        else:
            camera_obj.data.clip_start = 0.1 

        # --- Configuración del Track To Constraint ---
        constraint = camera_obj.constraints.new(type='TRACK_TO')
        constraint.name = "Track To Rocket" 
        constraint.target = rocket
        constraint.track_axis = 'TRACK_NEGATIVE_Z' 
        constraint.up_axis = 'UP_Y' 

        # --- Activar la cámara si el checkbox está marcado ---
        if props.set_top_camera_active:
            context.scene.camera = camera_obj
            bpy.ops.object.select_all(action='DESELECT')
            camera_obj.select_set(True)
            context.view_layer.objects.active = camera_obj

        self.report({'INFO'}, f"Cámara cenital '{camera_obj.name}' creada y configurada para '{rocket_name}'.")
        return {'FINISHED'}

# --- OPERADOR PARA ACTUALIZAR LA CÁMARA CENITAL EXISTENTE ---
class ORA_OT_UpdateRocketCamera(bpy.types.Operator):
    bl_idname = "object.ora_update_rocket_camera"
    bl_label = "Update Camera"
    bl_description = "Actualiza la posición y el clipping de la cámara cenital existente según los offsets. Solo actualiza la primera cámara llamada 'Rocket_Top_Camera'."

    def execute(self, context):
        props = context.scene.ora_props
        rocket_name = props.rocket_name

        # Nota: Este operador solo afecta a la cámara llamada "Rocket_Top_Camera"
        # Si se han creado múltiples cámaras, solo la primera (sin sufijo) será actualizada.
        camera_obj = bpy.data.objects.get("Rocket_Top_Camera")
        if not camera_obj:
            self.report({'ERROR'}, "No se encontró la cámara 'Rocket_Top_Camera'. Por favor, créala primero.")
            return {'CANCELLED'}
        
        rocket = bpy.data.objects.get(rocket_name)
        if not rocket:
            self.report({'ERROR'}, f"No se encontró un objeto llamado '{rocket_name}' para actualizar la cámara. El nombre del cohete puede haber cambiado o el objeto fue eliminado.")
            return {'CANCELLED'}

        if camera_obj.parent != rocket:
            camera_obj.parent = rocket
            self.report({'INFO'}, "La cámara 'Rocket_Top_Camera' ha sido re-emparentada al cohete especificado.")

        # Recalcular la posición local de la cámara (igual que en AddRocketCamera)
        bbox_corners_local = [Vector(corner) for corner in rocket.bound_box]
        bbox_max_z_local = max(v.z for v in bbox_corners_local)
        bbox_min_x_local = min(v.x for v in bbox_corners_local)
        bbox_max_x_local = max(v.x for v in bbox_corners_local)
        bbox_center_x_local = (bbox_min_x_local + bbox_max_x_local) / 2
        bbox_min_y_local = min(v.y for v in bbox_corners_local)
        bbox_max_y_local = max(v.y for v in bbox_corners_local)
        bbox_center_y_local = (bbox_min_y_local + bbox_max_y_local) / 2
        
        camera_obj.location.x = bbox_center_x_local + props.offset_x_camera
        camera_obj.location.y = bbox_center_y_local
        camera_obj.location.z = bbox_max_z_local + props.offset_z_camera

        # Re-aplicar rotación (por si acaso se cambió manualmente)
        camera_obj.rotation_euler = (0, 0, 0) 

        # Actualizar el clipping (igual que en AddRocketCamera)
        if props.adjust_clip_start:
            new_clip_start = abs(props.offset_z_camera) 
            if new_clip_start < 0.001:
                new_clip_start = 0.001
            camera_obj.data.clip_start = new_clip_start
        else:
            camera_obj.data.clip_start = 0.1 

        # Asegurarse de que el constraint exista antes de intentar modificarlo
        constraint = camera_obj.constraints.get("Track To Rocket")
        if constraint: # Si ya existe, lo actualizamos
            constraint.target = rocket # Asegurarse de que el target siga siendo el cohete
            constraint.track_axis = 'TRACK_NEGATIVE_Z' 
            constraint.up_axis = 'UP_Y' 
        else: # Si no existe (ej. fue borrado), lo creamos de nuevo
            constraint = camera_obj.constraints.new(type='TRACK_TO')
            constraint.name = "Track To Rocket"
            constraint.target = rocket
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'

        self.report({'INFO'}, "Cámara cenital 'Rocket_Top_Camera' actualizada.")
        return {'FINISHED'}

# --- OPERADOR PARA AÑADIR NOISE A LA CÁMARA ---
class ORA_OT_AddCameraNoise(bpy.types.Operator):
    bl_idname = "object.ora_add_camera_noise"
    bl_label = "Add Camera Noise"
    bl_description = "Añade un modificador Noise a las curvas de Location X/Y de la cámara seleccionada para simular vibración/dramatismo."

    def execute(self, context):
        props = context.scene.ora_props
        
        # --- Obtener la primera cámara seleccionada ---
        camera_obj = None
        for obj in context.selected_objects:
            if obj.type == 'CAMERA':
                camera_obj = obj
                break # Tomar la primera cámara seleccionada y salir del bucle
        
        if not camera_obj:
            self.report({'ERROR'}, "Por favor, selecciona una cámara en la escena para aplicar el ruido.")
            return {'CANCELLED'}

        # Asegurarse de que el objeto tenga animation_data
        if not camera_obj.animation_data:
            camera_obj.animation_data_create()
        # Asegurarse de que haya una Action, si no, crear una para la cámara seleccionada
        if not camera_obj.animation_data.action:
            camera_obj.animation_data.action = bpy.data.actions.new(name=f"{camera_obj.name}_Action")

        # Insertar un keyframe en la ubicación actual de la cámara para asegurar que las F-Curves existan
        # Esto crea las F-Curves para location.x, location.y, location.z si no están presentes.
        current_frame = context.scene.frame_current
        camera_obj.keyframe_insert(data_path="location", frame=current_frame)

        # Rutas de datos para las F-Curves de ubicación X e Y
        data_paths_and_indices = [
            ("location", 0), # location.x
            ("location", 1)  # location.y
        ] 

        for dp, idx in data_paths_and_indices:
            # Intentar encontrar la F-Curve existente
            fcurve = camera_obj.animation_data.action.fcurves.find(data_path=dp, index=idx)
            
            # Si la F-Curve no existe, crearla explícitamente
            if not fcurve:
                fcurve = camera_obj.animation_data.action.fcurves.new(data_path=dp, index=idx)
                # Opcional: Insertar un keyframe en esta F-Curve recién creada para darle un punto de partida
                # Aunque keyframe_insert("location") ya debería haberlo hecho para todas.
                fcurve.keyframe_points.insert(current_frame, camera_obj.location[idx])
                self.report({'INFO'}, f"F-Curve '{dp}' (índice {idx}) creada para la cámara '{camera_obj.name}'.")

            # Buscar si ya existe un modificador Noise en esta F-Curve
            noise_modifier = None
            for mod in fcurve.modifiers:
                if mod.type == 'NOISE':
                    noise_modifier = mod
                    break
            
            if not noise_modifier:
                # Si no existe, añadir uno nuevo
                noise_modifier = fcurve.modifiers.new(type='NOISE')
            
            # Configurar las propiedades del modificador Noise
            noise_modifier.strength = props.noise_strength
            noise_modifier.scale = props.noise_scale
            noise_modifier.depth = props.noise_depth
            noise_modifier.blend_type = 'REPLACE' 

            self.report({'INFO'}, f"Modificador Noise aplicado a la curva '{dp}' de la cámara '{camera_obj.name}'.")

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

        # --- Nuevo apartado para el Noise de la Cámara ---
        box_camera_noise = box4.box()
        box_camera_noise.label(text="Efecto 'Shake' de Cámara (Noise)") 
        box_camera_noise.prop(props, "noise_scale")
        box_camera_noise.prop(props, "noise_strength")
        box_camera_noise.prop(props, "noise_depth")
        box_camera_noise.operator("object.ora_add_camera_noise", text="Add Camera Noise / Shake")


# --- BLOQUE PARA DESARROLLO EN EL EDITOR DE TEXTO ---
# Esto asegura que las clases se desregistren antes de volver a registrarse
# cada vez que se pulsa "Run Script" (Alt+P), evitando errores y actualizando la UI.
if "bpy" in locals():
    # Lista de todas las clases que se registran en este script
    classes_to_reload = [
        OpenRocketAnimProps,
        ORA_OT_ImportOBJ,
        ORA_OT_FixScale,
        ORA_OT_AnimateFromCSV,
        ORA_OT_ConvertToLinear,
        ORA_OT_TrackRocket,
        ORA_OT_AddRocketCamera,
        ORA_OT_UpdateRocketCamera,
        ORA_OT_AddCameraNoise,
        ORA_PT_Panel
    ]
    
    for cls in classes_to_reload:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass # Ignora si la clase no estaba registrada (primera ejecución o error previo)

    # Elimina la propiedad de escena si ya existe para asegurar una re-creación limpia
    if hasattr(bpy.types.Scene, "ora_props"):
        del bpy.types.Scene.ora_props
# --- FIN BLOQUE PARA DESARROLLO ---


def register():
    bpy.utils.register_class(OpenRocketAnimProps)
    bpy.utils.register_class(ORA_OT_ImportOBJ)
    bpy.utils.register_class(ORA_OT_FixScale)
    bpy.utils.register_class(ORA_OT_AnimateFromCSV)
    bpy.utils.register_class(ORA_OT_ConvertToLinear)
    bpy.utils.register_class(ORA_OT_TrackRocket)
    bpy.utils.register_class(ORA_OT_AddRocketCamera)
    bpy.utils.register_class(ORA_OT_UpdateRocketCamera)
    bpy.utils.register_class(ORA_OT_AddCameraNoise) # Registrar el nuevo operador
    bpy.utils.register_class(ORA_PT_Panel)
    bpy.types.Scene.ora_props = bpy.props.PointerProperty(type=OpenRocketAnimProps)

def unregister():
    bpy.utils.unregister_class(OpenRocketAnimProps)
    bpy.utils.unregister_class(ORA_OT_ImportOBJ)
    bpy.utils.unregister_class(ORA_OT_FixScale)
    bpy.utils.unregister_class(ORA_OT_AnimateFromCSV)
    bpy.utils.unregister_class(ORA_OT_ConvertToLinear)
    bpy.utils.unregister_class(ORA_OT_TrackRocket)
    bpy.utils.unregister_class(ORA_OT_AddRocketCamera)
    bpy.utils.unregister_class(ORA_OT_UpdateRocketCamera)
    bpy.utils.unregister_class(ORA_OT_AddCameraNoise) # Desregistrar el nuevo operador
    del bpy.types.Scene.ora_props

if __name__ == "__main__":
    register()
