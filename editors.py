# editors.py
import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Menu, Operator

from .common import get_visible_tabs
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


class WM_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "WM_MT_quick_sidebar_switcher"
    bl_label = "Sidebar Tabs"
    SPACE_TYPES = SUPPORTED_SPACE_TYPES
    OP_SWITCH_NAME = "wm.quick_sidebar_switcher_switch"
    OP_SEARCH_NAME = "wm.quick_sidebar_switcher_search"


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    WM_OT_switch_sidebar_tab,
    WM_OT_sidebar_tab_menu,
    WM_OT_sidebar_tab_search,
    WM_MT_sidebar_tab_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
