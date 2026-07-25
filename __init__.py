bl_info = {
    "name": "Dissolve Objects",
    "description": "Dissolve selected objects while preserving their children's transforms.",
    "author": "Mathieu Richecoeur",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Object > Dissolve | Object Context Menu | Outliner Context Menu",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

"""Delete selected objects while preserving their children's transforms and 
hierarchy by reparenting them to the closest remaining parent.
Useful when editing nested object hierarchies.
Similar to Dissolve Bones for armatures.
Optionally skip parents with sheared transforms or parents with children 
that have sheared transforms, to avoid changing their visual appearance.

Based on an idea and request by 3D artist Enzo Ducos.
"""

import bpy


def set_parent_keep_transform(obj: bpy.types.Object, parent: bpy.types.Object | None):
    matrix_world = obj.matrix_world.copy()
    obj.parent = parent
    if obj.parent:
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = matrix_world


def has_shear(obj: bpy.types.Object, epsilon: float = 1e-5) -> bool:
    m = obj.matrix_world.to_3x3()

    x = m.col[0].normalized()
    y = m.col[1].normalized()
    z = m.col[2].normalized()

    return abs(x.dot(y)) > epsilon or abs(x.dot(z)) > epsilon or abs(y.dot(z)) > epsilon


def dissolve_object(obj: bpy.types.Object, del_global: bool = False):
    children = list(obj.children)
    for child in children:
        set_parent_keep_transform(child, None)

    if obj.parent:
        for child in children:
            set_parent_keep_transform(child, obj.parent)

    if del_global:
        bpy.data.objects.remove(obj)
    else:
        for col in obj.users_collection:
            col.objects.unlink(obj)


def filter_sheared(objects: list[bpy.types.Object]) -> list[bpy.types.Object]:
    """Remove parents with sheared transforms, or parents with children
    that have sheared transforms.
    """

    filtered = []
    for obj in objects:
        if not obj.children:
            filtered.append(obj)
            continue

        sheared = False
        if has_shear(obj):
            sheared = True
        for child in obj.children:

            if has_shear(child):
                sheared = True
                break
        if not sheared:
            filtered.append(obj)
    return filtered


class DO_OT_DissolveObject(bpy.types.Operator):
    bl_idname = "object.dissolve_selected_objects"
    bl_label = "Dissolve"
    bl_description = (
        "Delete selected objects while preserving their children's transforms and \n"
        "hierarchy by reparenting them to the closest remaining parent."
    )
    bl_options = {"REGISTER", "UNDO"}

    use_global: bpy.props.BoolProperty(
        name="Global Delete",
        description=(
            "Completely delete objects from the file instead of \n"
            "only removing them from the hierarchy."
        ),
        default=False,
    )  # type: ignore
    skip_sheared: bpy.props.BoolProperty(
        name="Skip Sheared",
        description=(
            "Do not delete parents with sheared transforms, or parents whose children "
            "have sheared transforms.\n"
            "Deleting such objects may change the visual appearance of their children"
        ),
        default=False,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        objects = context.selected_objects
        if self.skip_sheared:
            objects = filter_sheared(objects)

        for obj in objects:
            dissolve_object(obj, self.use_global)

        return {"FINISHED"}


def draw_object_menu(self, context):
    layout: bpy.types.UILayout = self.layout
    layout.separator()
    layout.operator(operator=DO_OT_DissolveObject.bl_idname)


def draw_outliner_menu(self, context):
    layout: bpy.types.UILayout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"  # Force operator menu
    layout.separator()
    layout.operator(operator=DO_OT_DissolveObject.bl_idname)


def register():
    bpy.utils.register_class(DO_OT_DissolveObject)

    try:
        bpy.types.VIEW3D_MT_object.remove(draw_object_menu)
        bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_menu)
        bpy.types.OUTLINER_MT_object.remove(draw_outliner_menu)
    except:
        pass

    bpy.types.VIEW3D_MT_object.append(draw_object_menu)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_menu)
    bpy.types.OUTLINER_MT_object.append(draw_outliner_menu)


def unregister():
    bpy.utils.unregister_class(DO_OT_DissolveObject)
    try:
        bpy.types.VIEW3D_MT_object.remove(draw_object_menu)
        bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_menu)
        bpy.types.OUTLINER_MT_object.remove(draw_outliner_menu)
    except:
        pass


if __name__ == "__main__":
    unregister()
    register()
