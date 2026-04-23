import os

import bpy


class ORA_OT_ImportOBJ(bpy.types.Operator):
    bl_idname = "object.ora_import_obj"
    bl_label = "Import OBJ"

    def execute(self, context):
        path = bpy.path.abspath(context.scene.ora_props.obj_filepath)
        if not os.path.exists(path):
            self.report({'ERROR'}, f"File not found: {path}")
            return {'CANCELLED'}

        try:
            bpy.ops.wm.obj_import(filepath=path)

            obj = context.view_layer.objects.active
            if obj:
                self.report({'INFO'}, "OBJ model imported successfully. Use Fix Scale if needed.")
        except Exception as exc:
            self.report({'ERROR'}, f"Error importing OBJ: {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}


class ORA_OT_FixScale(bpy.types.Operator):
    bl_idname = "object.ora_fix_scale"
    bl_label = "Fix Scale"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'ERROR'}, "No active object to scale.")
            return {'CANCELLED'}

        factor = context.scene.ora_props.default_scale_factor
        obj.scale = (factor, factor, factor)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        self.report({'INFO'}, f"Scale fixed and applied with factor {factor}.")
        return {'FINISHED'}


class ORA_OT_ClearRotation(bpy.types.Operator):
    bl_idname = "object.ora_clear_rotation"
    bl_label = "Clear Rotation"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'ERROR'}, "No active object to clear rotation.")
            return {'CANCELLED'}

        if obj.rotation_mode == 'QUATERNION':
            obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        elif obj.rotation_mode == 'AXIS_ANGLE':
            obj.rotation_axis_angle = (0.0, 0.0, 0.0, 1.0)
        else:
            obj.rotation_euler = (0.0, 0.0, 0.0)

        self.report({'INFO'}, "Rotation cleared for active object.")
        return {'FINISHED'}


classes = (
    ORA_OT_ImportOBJ,
    ORA_OT_FixScale,
    ORA_OT_ClearRotation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
