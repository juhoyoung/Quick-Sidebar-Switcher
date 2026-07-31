# operators.py
import bpy
from bpy.types import Operator, Menu
from .common import update_tabs, get_visible_tabs, switch_tab_logic

# ------------------------------------------------------------------------
# Base Abstract Classes (Template Factory Pattern)
# ------------------------------------------------------------------------
def resolve_space_type(cls, context):
    if cls.SPACE_TYPE:
        return cls.SPACE_TYPE

    space_type = getattr(context.area, "type", None)
    if cls.SPACE_TYPES and space_type in cls.SPACE_TYPES:
        return space_type
    return None


class BaseSwitchSidebarTabOp:
    """Abstract class for switching tabs."""
    bl_options = set()
    SPACE_TYPE = None
    SPACE_TYPES = None

    get_space_type = classmethod(resolve_space_type)

    def execute(self, context):
        space_type = self.get_space_type(context)
        if not space_type:
            return {'CANCELLED'}
        return switch_tab_logic(context, space_type, self.tab_name)

class BaseSidebarTabMenuOp:
    """Abstract class for opening the popup menu."""
    SPACE_TYPE = None
    SPACE_TYPES = None
    MENU_NAME = ""

    def invoke(self, context, event):
        space_type = resolve_space_type(self.__class__, context)
        if not space_type:
            return {'CANCELLED'}

        update_tabs(context, space_type)
        bpy.ops.wm.call_menu(name=self.MENU_NAME)
        return {'FINISHED'}

class BaseSidebarTabSearchOp:
    """Abstract class for searching tabs via popup."""
    bl_options = set()
    bl_property = "tab_enum"
    SPACE_TYPE = None
    SPACE_TYPES = None

    get_space_type = classmethod(resolve_space_type)

    @classmethod
    def poll(cls, context):
        return bool(cls.get_space_type(context))

    def execute(self, context):
        space_type = self.get_space_type(context)
        if not space_type:
            return {'CANCELLED'}

        if self.tab_enum and self.tab_enum != 'NONE':
            return switch_tab_logic(context, space_type, self.tab_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

class BaseSidebarTabMenu:
    """Abstract class for drawing the uniform menu interface."""
    SPACE_TYPE = None
    SPACE_TYPES = None
    OP_SWITCH_NAME = ""
    OP_SEARCH_NAME = ""

    get_space_type = classmethod(resolve_space_type)

    def draw(self, context):
        layout = self.layout
        top_col = layout.column()

        top_col.operator("wm.open_sidebar_switcher_prefs", text="Open Settings", icon='PREFERENCES')
        top_col.operator_context = 'INVOKE_DEFAULT'
        top_col.operator(self.OP_SEARCH_NAME, text="Search Tabs...", icon='VIEWZOOM')
        top_col.separator()

        try:
            prefs = context.preferences.addons[__package__].preferences
            columns = prefs.popup_columns
        except Exception:
            columns = 2

        space_type = self.get_space_type(context)
        tabs = get_visible_tabs(context, space_type) if space_type else []

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
