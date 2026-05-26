import bpy
from bpy.types import Operator, Menu
from bpy.props import StringProperty, EnumProperty
from .common import update_tabs, get_visible_tabs, get_tab_enum_items, switch_tab_logic

class VIEW3D_OT_switch_sidebar_tab(Operator):
    """Switch to a specific sidebar tab in 3D View"""
    bl_idname = "view3d.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    bl_options = set()

    tab_name: StringProperty()

    def execute(self, context):
        return switch_tab_logic(context, 'VIEW_3D', self.tab_name)

class VIEW3D_OT_sidebar_tab_menu(Operator):
    """Open a popup menu to select a sidebar tab in 3D View"""
    bl_idname = "view3d.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (3D View)"

    def invoke(self, context, event):
        update_tabs(context, 'VIEW_3D')
        bpy.ops.wm.call_menu(name="VIEW3D_MT_sidebar_tab_menu")
        return {'FINISHED'}

class VIEW3D_OT_sidebar_tab_search(Operator):
    """Search and select a sidebar tab in 3D View"""
    bl_idname = "view3d.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"
    bl_property = "tab_enum"

    tab_enum: EnumProperty(name="Tab", items=get_tab_enum_items)

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        if self.tab_enum and self.tab_enum != 'NONE':
            return switch_tab_logic(context, 'VIEW_3D', self.tab_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'CANCELLED'}

class VIEW3D_OT_open_addon_prefs(Operator):
    """Open Preferences for Quick Sidebar Switcher"""
    bl_idname = "view3d.open_sidebar_switcher_prefs"
    bl_label = "Open Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        context.window_manager.addon_search = "Quick Sidebar Switcher"
        context.preferences.active_section = 'ADDONS'
        return {'FINISHED'}

class VIEW3D_MT_sidebar_tab_menu(Menu):
    bl_label = "Sidebar Tabs"
    bl_idname = "VIEW3D_MT_sidebar_tab_menu"

    def draw(self, context):
        layout = self.layout
        top_col = layout.column()
        top_col.operator("view3d.open_sidebar_switcher_prefs", text="Open Settings", icon='PREFERENCES')
        top_col.operator_context = 'INVOKE_DEFAULT'
        top_col.operator("view3d.sidebar_tab_search", text="Search Tabs...", icon='VIEWZOOM')
        top_col.separator()

        try:
            prefs = context.preferences.addons[__package__].preferences
            sort_order = prefs.tab_sort_order
            columns = prefs.popup_columns
        except Exception:
            sort_order = 'ALPHABETICAL'
            columns = 2

        tabs = get_visible_tabs(context, 'VIEW_3D', sort_order)

        if not tabs:
            layout.label(text="No Sidebar Tabs Found")
        else:
            if columns > 1:
                flow = layout.column_flow(columns=columns)
                for tab in tabs:
                    op = flow.operator("view3d.switch_sidebar_tab", text=tab)
                    op.tab_name = tab
            else:
                for tab in tabs:
                    op = layout.operator("view3d.switch_sidebar_tab", text=tab)
                    op.tab_name = tab

classes = (
    VIEW3D_OT_switch_sidebar_tab,
    VIEW3D_OT_sidebar_tab_menu,
    VIEW3D_OT_sidebar_tab_search,
    VIEW3D_OT_open_addon_prefs,
    VIEW3D_MT_sidebar_tab_menu,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)