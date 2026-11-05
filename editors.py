# editors.py
import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Menu, Operator

from .common import get_visible_tabs, open_sidebar_tab_popup
from .operators import (
    BaseSidebarTabMenu,
    BaseSidebarTabMenuOp,
    BaseSidebarTabSearchOp,
    BaseSwitchSidebarTabOp,
)


# ------------------------------------------------------------------------
# Supported Editors
# ------------------------------------------------------------------------
SUPPORTED_SPACE_TYPES = {
    'VIEW_3D',
    'NODE_EDITOR',
    'DOPESHEET_EDITOR',
    'GRAPH_EDITOR',
    'IMAGE_EDITOR',
}

LEGACY_MENU_OPERATORS = (
    ("VIEW3D_OT_sidebar_tab_menu", "view3d.sidebar_tab_menu", 'VIEW_3D'),
    ("NODE_OT_sidebar_tab_menu", "node.sidebar_tab_menu", 'NODE_EDITOR'),
    ("DOPESHEET_OT_sidebar_tab_menu", "dopesheet.sidebar_tab_menu", 'DOPESHEET_EDITOR'),
    ("GRAPH_OT_sidebar_tab_menu", "graph.sidebar_tab_menu", 'GRAPH_EDITOR'),
    ("IMAGE_OT_sidebar_tab_menu", "image.sidebar_tab_menu", 'IMAGE_EDITOR'),
)


def get_sidebar_tabs(self, context):
    space_type = getattr(context.area, "type", None)
    if space_type not in SUPPORTED_SPACE_TYPES:
        return [('NONE', 'No Tabs', '')]

    tabs = get_visible_tabs(context, space_type)
    return [(tab, tab, "") for tab in tabs] if tabs else [('NONE', 'No Tabs', '')]


# ------------------------------------------------------------------------
# Shared Editor Operators and Menu
# ------------------------------------------------------------------------
class WM_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "wm.quick_sidebar_switcher_switch"
    bl_label = "Switch Sidebar Tab"
    bl_description = "Select a sidebar tab; use the configured modifier-click to open a panel popup"
    SPACE_TYPES = SUPPORTED_SPACE_TYPES

    tab_name: StringProperty()


class WM_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "wm.quick_sidebar_switcher_menu"
    bl_label = "Open Sidebar Tabs"
    SPACE_TYPES = SUPPORTED_SPACE_TYPES
    MENU_NAME = "WM_MT_quick_sidebar_switcher"


class WM_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "wm.quick_sidebar_switcher_search"
    bl_label = "Search Sidebar Tabs"
    bl_property = "tab_enum"
    SPACE_TYPES = SUPPORTED_SPACE_TYPES

    tab_enum: EnumProperty(name="Tab", items=get_sidebar_tabs)


class WM_OT_sidebar_panel_popup(Operator):
    """Open a panel popup from the sidebar tab list using its configured shortcut"""
    bl_idname = "wm.quick_sidebar_switcher_panel_popup"
    bl_label = "Open Panel Popup (Tab List)"
    bl_description = "Open a panel popup when selecting a tab with this shortcut"

    tab_name: StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        if not self.tab_name or not context.area:
            return {'CANCELLED'}
        return open_sidebar_tab_popup(context, context.area.type, self.tab_name)


class WM_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "WM_MT_quick_sidebar_switcher"
    bl_label = "Sidebar Tabs"
    SPACE_TYPES = SUPPORTED_SPACE_TYPES
    OP_SWITCH_NAME = "wm.quick_sidebar_switcher_switch"
    OP_SEARCH_NAME = "wm.quick_sidebar_switcher_search"


# Preserve existing keymaps while forwarding all behavior to the shared menu.
def _create_legacy_menu_operator(class_name, operator_idname, space_type):
    return type(
        class_name,
        (BaseSidebarTabMenuOp, Operator),
        {
            "__module__": __name__,
            "bl_idname": operator_idname,
            "bl_label": "Open Sidebar Tabs",
            "SPACE_TYPE": space_type,
            "MENU_NAME": WM_MT_sidebar_tab_menu.bl_idname,
        },
    )


legacy_menu_classes = tuple(
    _create_legacy_menu_operator(*operator_spec)
    for operator_spec in LEGACY_MENU_OPERATORS
)


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    WM_OT_switch_sidebar_tab,
    WM_OT_sidebar_tab_menu,
    WM_OT_sidebar_tab_search,
    WM_OT_sidebar_panel_popup,
    WM_MT_sidebar_tab_menu,
    *legacy_menu_classes,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
