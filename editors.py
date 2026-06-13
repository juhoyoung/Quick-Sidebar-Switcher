# editors.py
import bpy
from bpy.types import Operator, Menu
from bpy.props import StringProperty, EnumProperty

from .operators import (
    BaseSwitchSidebarTabOp,
    BaseSidebarTabMenuOp,
    BaseSidebarTabSearchOp,
    BaseSidebarTabMenu
)
from .common import get_visible_tabs

# ------------------------------------------------------------------------
# Explicit Callbacks for EnumProperty Items
# ------------------------------------------------------------------------
def get_view3d_tabs(self, context):
    tabs = get_visible_tabs(context, 'VIEW_3D')
    return [(t, t, "") for t in tabs] if tabs else [('NONE', 'No Tabs', '')]

def get_node_tabs(self, context):
    tabs = get_visible_tabs(context, 'NODE_EDITOR')
    return [(t, t, "") for t in tabs] if tabs else [('NONE', 'No Tabs', '')]

def get_dopesheet_tabs(self, context):
    tabs = get_visible_tabs(context, 'DOPESHEET_EDITOR')
    return [(t, t, "") for t in tabs] if tabs else [('NONE', 'No Tabs', '')]

def get_graph_tabs(self, context):
    tabs = get_visible_tabs(context, 'GRAPH_EDITOR')
    return [(t, t, "") for t in tabs] if tabs else [('NONE', 'No Tabs', '')]
def get_image_tabs(self, context):
    tabs = get_visible_tabs(context, 'IMAGE_EDITOR')
    return [(t, t, "") for t in tabs] if tabs else [('NONE', 'No Tabs', '')]

# ------------------------------------------------------------------------
# 1. 3D Viewport
# ------------------------------------------------------------------------
class VIEW3D_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "view3d.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    SPACE_TYPE = 'VIEW_3D'

    tab_name: StringProperty()

class VIEW3D_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "view3d.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (3D View)"
    SPACE_TYPE = 'VIEW_3D'
    MENU_NAME = "VIEW3D_MT_sidebar_tab_menu"

class VIEW3D_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "view3d.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"

    # Explicitly declared here so Blender's UI engine recognizes it
    bl_property = "tab_enum"
    SPACE_TYPE = 'VIEW_3D'

    tab_enum: EnumProperty(name="Tab", items=get_view3d_tabs)

class VIEW3D_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "VIEW3D_MT_sidebar_tab_menu"
    bl_label = "Sidebar Tabs"
    SPACE_TYPE = 'VIEW_3D'
    OP_SWITCH_NAME = "view3d.switch_sidebar_tab"
    OP_SEARCH_NAME = "view3d.sidebar_tab_search"

# ------------------------------------------------------------------------
# 2. Node Editor (Shader, Compositor, Geometry Nodes)
# ------------------------------------------------------------------------
class NODE_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "node.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    SPACE_TYPE = 'NODE_EDITOR'

    tab_name: StringProperty()

class NODE_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "node.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (Node Editor)"
    SPACE_TYPE = 'NODE_EDITOR'
    MENU_NAME = "NODE_MT_sidebar_tab_menu"

class NODE_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "node.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"

    # Explicitly declared here so Blender's UI engine recognizes it
    bl_property = "tab_enum"
    SPACE_TYPE = 'NODE_EDITOR'

    tab_enum: EnumProperty(name="Tab", items=get_node_tabs)

class NODE_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "NODE_MT_sidebar_tab_menu"
    bl_label = "Node Editor Tabs"
    SPACE_TYPE = 'NODE_EDITOR'
    OP_SWITCH_NAME = "node.switch_sidebar_tab"
    OP_SEARCH_NAME = "node.sidebar_tab_search"

# ------------------------------------------------------------------------
# 3. Dopesheet Editor
# ------------------------------------------------------------------------
class DOPESHEET_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "dopesheet.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    SPACE_TYPE = 'DOPESHEET_EDITOR'

    tab_name: StringProperty()

class DOPESHEET_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "dopesheet.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (Dopesheet)"
    SPACE_TYPE = 'DOPESHEET_EDITOR'
    MENU_NAME = "DOPESHEET_MT_sidebar_tab_menu"

class DOPESHEET_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "dopesheet.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"

    # Explicitly declared here so Blender's UI engine recognizes it
    bl_property = "tab_enum"
    SPACE_TYPE = 'DOPESHEET_EDITOR'

    tab_enum: EnumProperty(name="Tab", items=get_dopesheet_tabs)

class DOPESHEET_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "DOPESHEET_MT_sidebar_tab_menu"
    bl_label = "Dopesheet Tabs"
    SPACE_TYPE = 'DOPESHEET_EDITOR'
    OP_SWITCH_NAME = "dopesheet.switch_sidebar_tab"
    OP_SEARCH_NAME = "dopesheet.sidebar_tab_search"

# ------------------------------------------------------------------------
# 4. Graph Editor
# ------------------------------------------------------------------------
class GRAPH_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "graph.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    SPACE_TYPE = 'GRAPH_EDITOR'
    tab_name: StringProperty()

class GRAPH_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "graph.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (Graph Editor)"
    SPACE_TYPE = 'GRAPH_EDITOR'
    MENU_NAME = "GRAPH_MT_sidebar_tab_menu"

class GRAPH_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "graph.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"
    bl_property = "tab_enum"
    SPACE_TYPE = 'GRAPH_EDITOR'
    tab_enum: EnumProperty(name="Tab", items=get_graph_tabs)

class GRAPH_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "GRAPH_MT_sidebar_tab_menu"
    bl_label = "Graph Editor Tabs"
    SPACE_TYPE = 'GRAPH_EDITOR'
    OP_SWITCH_NAME = "graph.switch_sidebar_tab"
    OP_SEARCH_NAME = "graph.sidebar_tab_search"

# ------------------------------------------------------------------------
# 5. Image / UV Editor
# ------------------------------------------------------------------------
class IMAGE_OT_switch_sidebar_tab(BaseSwitchSidebarTabOp, Operator):
    bl_idname = "image.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    SPACE_TYPE = 'IMAGE_EDITOR'
    tab_name: StringProperty()

class IMAGE_OT_sidebar_tab_menu(BaseSidebarTabMenuOp, Operator):
    bl_idname = "image.sidebar_tab_menu"
    bl_label = "Open Sidebar Tab (Image/UV)"
    SPACE_TYPE = 'IMAGE_EDITOR'
    MENU_NAME = "IMAGE_MT_sidebar_tab_menu"

class IMAGE_OT_sidebar_tab_search(BaseSidebarTabSearchOp, Operator):
    bl_idname = "image.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"
    bl_property = "tab_enum"
    SPACE_TYPE = 'IMAGE_EDITOR'
    tab_enum: EnumProperty(name="Tab", items=get_image_tabs)

class IMAGE_MT_sidebar_tab_menu(BaseSidebarTabMenu, Menu):
    bl_idname = "IMAGE_MT_sidebar_tab_menu"
    bl_label = "Image/UV Editor Tabs"
    SPACE_TYPE = 'IMAGE_EDITOR'
    OP_SWITCH_NAME = "image.switch_sidebar_tab"
    OP_SEARCH_NAME = "image.sidebar_tab_search"

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    VIEW3D_OT_switch_sidebar_tab,
    VIEW3D_OT_sidebar_tab_menu,
    VIEW3D_OT_sidebar_tab_search,
    VIEW3D_MT_sidebar_tab_menu,

    NODE_OT_switch_sidebar_tab,
    NODE_OT_sidebar_tab_menu,
    NODE_OT_sidebar_tab_search,
    NODE_MT_sidebar_tab_menu,

    DOPESHEET_OT_switch_sidebar_tab,
    DOPESHEET_OT_sidebar_tab_menu,
    DOPESHEET_OT_sidebar_tab_search,
    DOPESHEET_MT_sidebar_tab_menu,

    GRAPH_OT_switch_sidebar_tab,
    GRAPH_OT_sidebar_tab_menu,
    GRAPH_OT_sidebar_tab_search,
    GRAPH_MT_sidebar_tab_menu,

    IMAGE_OT_switch_sidebar_tab,
    IMAGE_OT_sidebar_tab_menu,
    IMAGE_OT_sidebar_tab_search,
    IMAGE_MT_sidebar_tab_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)