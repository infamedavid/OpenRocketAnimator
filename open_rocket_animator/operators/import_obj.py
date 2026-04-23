import os

import bpy


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
        except Exception as exc:
            self.report({'ERROR'}, f"Error al importar OBJ: {exc}")
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


classes = (
    ORA_OT_ImportOBJ,
    ORA_OT_FixScale,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
