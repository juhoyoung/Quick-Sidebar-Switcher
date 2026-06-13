# operators.py
import bpy
from bpy.types import Operator, Menu
from .common import update_tabs, get_visible_tabs, switch_tab_logic

# ------------------------------------------------------------------------
# Base Abstract Classes (Template Factory Pattern)
# ------------------------------------------------------------------------
class BaseSwitchSidebarTabOp:
    """Abstract class for switching tabs."""
    bl_options = set()
    SPACE_TYPE = 'VIEW_3D' # To be overridden

    # Note: tab_name: StringProperty() is removed here.
    # Blender requires RNA properties to be declared on the registered child class.

    def execute(self, context):
        return switch_tab_logic(context, self.SPACE_TYPE, self.tab_name)

class BaseSidebarTabMenuOp:
    """Abstract class for opening the popup menu."""
    SPACE_TYPE = 'VIEW_3D' # To be overridden
    MENU_NAME = ""         # To be overridden

    def invoke(self, context, event):
        update_tabs(context, self.SPACE_TYPE)
        bpy.ops.wm.call_menu(name=self.MENU_NAME)
        return {'FINISHED'}

class BaseSidebarTabSearchOp:
    """Abstract class for searching tabs via popup."""
    bl_options = set()
    bl_property = "tab_enum"
    SPACE_TYPE = 'VIEW_3D' # To be overridden

    # Note: tab_enum: EnumProperty() is also removed here for the same reason.

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == cls.SPACE_TYPE

    def execute(self, context):
        if self.tab_enum and self.tab_enum != 'NONE':
            return switch_tab_logic(context, self.SPACE_TYPE, self.tab_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'CANCELLED'}

class BaseSidebarTabMenu:
    """Abstract class for drawing the uniform menu interface."""
    SPACE_TYPE = 'VIEW_3D'       # To be overridden
    OP_SWITCH_NAME = ""          # To be overridden
    OP_SEARCH_NAME = ""          # To be overridden

    def draw(self, context):
        layout = self.layout
        top_col = layout.column()

        top_col.operator("wm.open_sidebar_switcher_prefs", text="Open Settings", icon='PREFERENCES')
        top_col.operator_context = 'INVOKE_DEFAULT'
        top_col.operator(self.OP_SEARCH_NAME, text="Search Tabs...", icon='VIEWZOOM')
        top_col.separator()

        try:
            prefs = context.preferences.addons[__package__].preferences
            sort_order = prefs.tab_sort_order
            columns = prefs.popup_columns
        except Exception:
            sort_order = 'ALPHABETICAL'
            columns = 2

        tabs = get_visible_tabs(context, self.SPACE_TYPE, sort_order)

        if not tabs:
            layout.label(text="No Sidebar Tabs Found")
        else:
            if columns > 1:
                flow = layout.column_flow(columns=columns)
                for tab in tabs:
                    op = flow.operator(self.OP_SWITCH_NAME, text=tab)
                    op.tab_name = tab
            else:
                for tab in tabs:
                    op = layout.operator(self.OP_SWITCH_NAME, text=tab)
                    op.tab_name = tab

# ------------------------------------------------------------------------
# Global Shared Operator
# ------------------------------------------------------------------------
class WM_OT_open_sidebar_switcher_prefs(Operator):
    """Open Preferences for Quick Sidebar Switcher"""
    bl_idname = "wm.open_sidebar_switcher_prefs"
    bl_label = "Open Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        context.window_manager.addon_search = "Quick Sidebar Switcher"
        context.preferences.active_section = 'ADDONS'
        return {'FINISHED'}


classes = (
    WM_OT_open_sidebar_switcher_prefs,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)